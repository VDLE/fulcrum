"""Task queue for async analytics processing"""

import os
import logging
import redis
from rq import Queue
from rq.job import Job
from datetime import datetime, timedelta
import json
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Cache configuration
RESULT_CACHE_TTL = 3600  # 1 hour
# Connection configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Initialize two Redis connections - one for direct Redis operations (with decoding) and one for RQ (without decoding)
try:
    logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")

    # Connection for direct Redis operations (with decoding)
    # Use explicit True for decode_responses to ensure it's properly set
    redis_conn = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,  # Auto-decode for our direct operations (explicit True)
        socket_timeout=5,  # 5 second timeout for operations
        socket_connect_timeout=5,  # 5 second timeout for connection
    )

    # Connection for RQ (without decoding, as it needs binary responses)
    rq_redis_conn = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=False,  # Important: RQ needs binary responses
        socket_timeout=5,
        socket_connect_timeout=5,
    )

    redis_conn.ping()  # Test connection
    logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    # Use a fallback for development/testing
    logger.warning(
        "Using mock Redis for development/testing - jobs will execute synchronously"
    )
    redis_conn = None
    rq_redis_conn = None

# Create RQ queue with the non-decoding Redis connection
try:
    if rq_redis_conn:
        queue = Queue("analytics", connection=rq_redis_conn)
        # Check if the queue is accessible
        job_count = queue.count
        logger.info(f"Analytics task queue initialized with {job_count} jobs waiting")
    else:
        queue = None
        logger.warning("No queue available - will process jobs synchronously")
except Exception as e:
    logger.error(f"Failed to initialize task queue: {str(e)}")
    queue = None
    logger.warning("Queue initialization failed - will process jobs synchronously")


# Job status constants
class JobStatus:
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_FOUND = "not_found"


# Cache for result storage
result_cache = {}


def enqueue_task(func, *args, **kwargs):
    """Enqueue task for async processing, returns job info dict"""
    if queue is None:
        # Fallback to synchronous execution if queue is not available
        logger.warning("Queue not available, executing task synchronously")
        try:
            # Generate a unique job ID for tracking
            job_id = str(uuid.uuid4())

            # Log what we're about to do
            arg_str = ", ".join([str(arg) for arg in args])
            kwarg_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            logger.info(
                f"Executing {func.__name__}({arg_str}{', ' if arg_str and kwarg_str else ''}{kwarg_str}) synchronously with job ID {job_id}"
            )

            # Execute the function
            result = func(*args, **kwargs)

            # Cache the result
            store_result(job_id, result)

            logger.info(f"Synchronous execution completed for job {job_id}")

            return {"job_id": job_id, "status": JobStatus.COMPLETED, "result": result}
        except Exception as e:
            error_job_id = str(uuid.uuid4())
            logger.error(
                f"Error executing task synchronously (job {error_job_id}): {str(e)}"
            )
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")

            # Try to get a traceback for better debugging
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            return {
                "job_id": error_job_id,
                "status": JobStatus.FAILED,
                "error": f"{type(e).__name__}: {str(e)}",
            }

    try:
        # Add task metadata to kwargs
        kwargs["_job_meta"] = {
            "enqueued_at": datetime.now().isoformat(),
            "description": f"{func.__name__} task",
            "args": str(args),
            "kwargs": str({k: v for k, v in kwargs.items() if k != "_job_meta"}),
        }

        # Log what we're about to enqueue
        arg_str = ", ".join([str(arg) for arg in args])
        kwarg_str = ", ".join(
            [f"{k}={v}" for k, v in kwargs.items() if k != "_job_meta"]
        )
        logger.info(
            f"Enqueueing {func.__name__}({arg_str}{', ' if arg_str and kwarg_str else ''}{kwarg_str})"
        )

        # Enqueue the task
        job = queue.enqueue(
            func,
            *args,
            **kwargs,
            job_timeout=1200,  # 20 minutes timeout for large datasets
            result_ttl=3600,  # Keep results for 1 hour
        )

        logger.info(f"Successfully enqueued task {func.__name__} with job ID {job.id}")

        return {"job_id": job.id, "status": JobStatus.QUEUED}
    except Exception as e:
        logger.error(f"Error enqueueing task: {str(e)}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")

        # Try to get a traceback for better debugging
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        # Generate a job ID for the error
        error_job_id = str(uuid.uuid4())

        return {
            "job_id": error_job_id,
            "status": JobStatus.FAILED,
            "error": f"{type(e).__name__}: {str(e)}",
        }


def get_job_status(job_id):
    """Check job status by ID, returns status info dict"""
    # First check if the result is in our cache
    if job_id in result_cache:
        logger.info(f"Found cached result for job {job_id}")
        return {
            "job_id": job_id,
            "status": JobStatus.COMPLETED,
            "result": result_cache[job_id]["data"],
        }

    # If we have no Redis connection, job can't be found
    if queue is None or rq_redis_conn is None:
        logger.warning(f"No queue available, job {job_id} not found")
        return {"job_id": job_id, "status": JobStatus.NOT_FOUND}

    try:
        # Check if result might be in Redis but not in memory cache
        redis_result = None
        if redis_conn:
            redis_key = f"result:{job_id}"
            result_json = redis_conn.get(redis_key)
            if result_json:
                try:
                    result_data = json.loads(result_json)
                    redis_result = result_data["data"]
                    logger.info(f"Found result in Redis for job {job_id}")

                    # Also store in memory cache for faster future access
                    result_cache[job_id] = {
                        "data": redis_result,
                        "timestamp": datetime.now(),
                    }

                    return {
                        "job_id": job_id,
                        "status": JobStatus.COMPLETED,
                        "result": redis_result,
                    }
                except Exception as redis_err:
                    logger.error(
                        f"Error parsing Redis result for job {job_id}: {str(redis_err)}"
                    )

        # If not in cache, fetch job status using the RQ-specific Redis connection
        job = Job.fetch(job_id, connection=rq_redis_conn)
        logger.info(
            f"Fetched job {job_id} status: {'finished' if job.is_finished else 'running' if job.is_started else 'queued'}"
        )

        if job.is_finished:
            # Job completed successfully
            result = job.result
            # Cache the result
            store_result(job_id, result)
            logger.info(f"Job {job_id} completed successfully, result stored in cache")
            return {"job_id": job_id, "status": JobStatus.COMPLETED, "result": result}
        elif job.is_failed:
            # Job failed
            error_msg = str(job.exc_info) if job.exc_info else "Unknown error"
            logger.error(f"Job {job_id} failed with error: {error_msg}")
            return {"job_id": job_id, "status": JobStatus.FAILED, "error": error_msg}
        elif job.is_started:
            # Job is running
            logger.info(f"Job {job_id} is currently running")
            return {"job_id": job_id, "status": JobStatus.RUNNING}
        else:
            # Job is queued
            logger.info(f"Job {job_id} is queued")
            return {"job_id": job_id, "status": JobStatus.QUEUED}
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {str(e)}")
        return {"job_id": job_id, "status": JobStatus.NOT_FOUND, "error": str(e)}


def store_result(job_id, result):
    """Cache job results in memory and Redis"""
    try:
        # Extract study_id for indexing if available
        study_id = None
        if isinstance(result, dict) and "study_id" in result:
            study_id = result["study_id"]
            logger.info(f"Found study_id={study_id} in job result for indexing")

        # Store in memory cache
        result_cache[job_id] = {
            "data": result,
            "timestamp": datetime.now(),
            "study_id": study_id,
        }

        # Clean up old cache entries
        clean_result_cache()

        # If Redis is available, also store there with TTL
        if redis_conn:
            try:
                # Check for completion_times data at the top level
                completion_metrics = None
                if isinstance(result, dict):
                    # Check if we have direct metrics at the top level
                    direct_metrics = {}
                    if (
                        "avg_completion_time" in result
                        and result["avg_completion_time"]
                    ):
                        direct_metrics["avg_completion_time"] = result[
                            "avg_completion_time"
                        ]

                    if "p_value" in result and result["p_value"]:
                        direct_metrics["p_value"] = result["p_value"]

                    # Check for nested completion_times
                    if "completion_times" in result and result["completion_times"]:
                        completion_times = result["completion_times"]

                        # Promote important metrics to the top level for easier access
                        if (
                            "avg_time" in completion_times
                            and completion_times["avg_time"]
                            and "avg_completion_time" not in direct_metrics
                        ):
                            result["avg_completion_time"] = completion_times["avg_time"]

                        if (
                            "p_value" in completion_times
                            and completion_times["p_value"]
                            and "p_value" not in direct_metrics
                        ):
                            result["p_value"] = completion_times["p_value"]

                # Convert result to JSON string
                result_json = json.dumps(
                    {
                        "data": result,
                        "timestamp": datetime.now().isoformat(),
                        "study_id": study_id,
                    },
                    default=str,
                )  # Use str for non-serializable objects

                # Store with TTL indexed by job_id
                redis_conn.setex(f"result:{job_id}", RESULT_CACHE_TTL, result_json)
                logger.info(f"Stored result for job {job_id} in Redis")

                # Also store indexed by study_id if available (for direct lookups)
                if study_id:
                    redis_conn.setex(
                        f"study:{study_id}:latest_result", RESULT_CACHE_TTL, result_json
                    )
                    logger.info(f"Also indexed result by study_id={study_id}")
            except Exception as json_err:
                logger.error(f"Error serializing job result to JSON: {str(json_err)}")
                # Store a simplified version
                try:
                    # Create a simplified version without complex objects
                    simple_result = {
                        "error": "Could not serialize full result",
                        "study_id": study_id,
                    }
                    redis_conn.setex(
                        f"result:{job_id}", RESULT_CACHE_TTL, json.dumps(simple_result)
                    )
                except:
                    logger.error("Could not store even simplified result")

        logger.debug(f"Stored result for job {job_id}")
    except Exception as e:
        logger.error(f"Error storing result for job {job_id}: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())


def get_result(job_id):
    """Retrieve cached result by job ID"""
    # First check memory cache
    if job_id in result_cache:
        return result_cache[job_id]["data"]

    # If not in memory but Redis is available, check there
    if redis_conn:
        try:
            result_json = redis_conn.get(f"result:{job_id}")
            if result_json:
                result_data = json.loads(result_json)
                # Also store in memory cache
                result_cache[job_id] = {
                    "data": result_data["data"],
                    "timestamp": datetime.fromisoformat(result_data["timestamp"]),
                }
                return result_data["data"]
        except Exception as e:
            logger.error(
                f"Error retrieving result from Redis for job {job_id}: {str(e)}"
            )

    # Result not found
    return None


def clean_result_cache():
    """Remove expired entries from cache"""
    now = datetime.now()
    expired_keys = []

    # Find expired keys
    for job_id, entry in result_cache.items():
        if now - entry["timestamp"] > timedelta(seconds=RESULT_CACHE_TTL):
            expired_keys.append(job_id)

    # Remove expired keys
    for job_id in expired_keys:
        del result_cache[job_id]

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
