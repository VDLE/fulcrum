import json
import random
import time
from itertools import product, permutations, combinations
from hashlib import sha256
from math import factorial
from collections import Counter


# Converting permutations to a hash value to compare against to check for uniqueness
def calc_perm_hash(trial_sequence):
    return sha256(json.dumps(trial_sequence).encode()).hexdigest()


# Calculating the number of unique permutations given a list of elements that may contain non-unique items
def calc_unique_perms(elements):
    denominator = 1
    counts = Counter(elements)
    n = sum(counts.values())
    for count in counts.values():
        denominator *= factorial(count)

    return factorial(n) // denominator


# Generates the permutation, using diff methods based on desired trial count for improved efficiency when searching for unused sequences
def generate_perm(
    unique_trial_options, trial_count, unique_requested, used_perms, iterations_needed=1
):
    unique_trial_count = len(unique_trial_options)

    """
    Constructing a base pool attempts to ensure an even spread of unique trials
    Ex. If we want 9 trials and we have 4 unique options, each option should appear twice with a remainder of 1 that will repeat a third time
    """
    base_pool = unique_trial_options * (trial_count // unique_trial_count)

    # Remainder count
    unbalanced_trial_count = trial_count % unique_trial_count
    # Stores the possible combos that can make up the remainders or "unbalanced" trials
    unbalanced_trial_combos = [()]
    if unbalanced_trial_count > 0:
        unbalanced_trial_combos = list(
            combinations(unique_trial_options, unbalanced_trial_count)
        )

    # Default to grabbing the first randomly generated permutation if uniqueness not required
    if not unique_requested:
        rand_combo = random.choice(unbalanced_trial_combos)
        full_pool = base_pool + list(rand_combo)
        random.shuffle(full_pool)
        return full_pool, "success"

    # Checking to see if we exhausted all possible unique permutations before searching for a new one
    sample_pool = base_pool + list(random.choice(unbalanced_trial_combos))
    max_unique_perms = (
        calc_unique_perms(sample_pool) * len(unbalanced_trial_combos)
    ) * iterations_needed
    num_unique_used_perms = len(set(used_perms))
    # print(f"Unique Possibilities: {max_unique_perms}")
    if num_unique_used_perms >= max_unique_perms:
        return None, "exhausted"

    # For short sequence lengths, generating all perms upfront is not too expensive and better when searching for an unused one
    if trial_count <= 4:
        random.shuffle(unbalanced_trial_combos)
        for combo in unbalanced_trial_combos:
            full_pool = base_pool + list(combo)

            # All possible perms found upfront
            all_perms = list(permutations(full_pool))
            random.shuffle(all_perms)

            for perm in all_perms:
                perm_hash = calc_perm_hash(perm)

                # Found an unused perm
                if perm_hash not in used_perms:
                    return list(perm), "success"

    # Too expensive to compute all perms upfront long sequences (factorial problem), but with a large pool repeats are unlikely so generate one at random and check it
    else:
        start_time = time.time()
        timeout = 5
        attempts = 0
        # Avoid getting stuck infinitely searching with a timeout (possible to replace this with an attempt limit instead)
        while time.time() - start_time < timeout:
            rand_combo = random.choice(unbalanced_trial_combos)

            full_pool = base_pool + list(rand_combo)
            random.shuffle(full_pool)
            perm_hash = calc_perm_hash(full_pool)

            # Found an unused perm!
            if perm_hash not in used_perms:
                return full_pool, "success"

            # Otherwise we keep looking until all combos have been checked or timeout reached
            attempts += 1
            # print(f"searching again... (attempt {attempts})")

    return None, "timeout"


# Logic for Within study types
def get_within_perm(tasks, factors, trial_count, used_perms):
    unique_trial_options = list(product(tasks, factors))
    within_perm, status = generate_perm(
        unique_trial_options, trial_count, True, used_perms, 1
    )

    if status == "exhausted":
        # Default to returning a non-unique random perm since all unique options used already
        within_perm, status = generate_perm(
            unique_trial_options, trial_count, False, used_perms, 1
        )
        return within_perm, "exhausted_fallback"

    if status == "timeout":
        # Failed to find a unique perm not due to exhaustion but timeout, so default to finding a random permutation (as done above)
        within_perm, status = generate_perm(
            unique_trial_options, trial_count, False, used_perms, 1
        )
        return within_perm, "timeout_fallback"

    if status == "success":
        return within_perm, "success"


# Logic for Between study types
def get_between_perm(tasks, factors, trial_count, used_perms):
    """
    Biggest difference compared to Within is we can only use 1 factor at a time
    Requires we search through all factors and consider exhaustion on a factor-to-factor basis
    """
    unchecked_factors = factors.copy()
    random.shuffle(unchecked_factors)
    num_factors_to_check = len(factors)

    all_factors_exhausted = True
    timeout_occured = False

    # Considering factors one at a time
    while unchecked_factors:
        index = random.randrange(len(unchecked_factors))
        rand_factor = unchecked_factors.pop(index)

        # Generates a pool with only 1 factor appearing in the elements
        unique_trial_options = list(product(tasks, [rand_factor]))
        between_perm, status = generate_perm(
            unique_trial_options, trial_count, True, used_perms, num_factors_to_check
        )

        if status == "success":
            return between_perm, "success"

        elif status == "timeout":
            timeout_occured = True
            all_factors_exhausted = False

        elif status == "exhausted":
            continue

        else:  # Different error occured
            all_factors_exhausted = False

    # Failed to find a unique perm so default to a perm that may not be unique (grab first one generated)
    fallback_factor = random.choice(factors)
    fallback_trials = list(product(tasks, [fallback_factor]))
    fallback_perm, _ = generate_perm(fallback_trials, trial_count, False, used_perms, 1)

    if all_factors_exhausted:
        return fallback_perm, "exhausted_fallback"
    elif timeout_occured:
        return fallback_perm, "timeout_fallback"
    else:
        return fallback_perm, "error"


# # Will want to get rid of this and build a test for this eventually for debugging
# if __name__ == "__main__":
#     # Sample values for the time being
#     task_list = [1, 2] # These are example ids
#     factors_list = [3, 4]
#     study_type = 'Within'
#     trial_count = 1
#     used_perms = set()

#     for i in range(25):
#         if study_type == 'Within':
#             perm, status = get_within_perm(task_list, factors_list, trial_count, used_perms)
#         else:
#             perm, status = get_between_perm(task_list, factors_list, trial_count, used_perms)

#         print(f"Perm Generated: {perm} \t Status: {status}")

#         perm_hash_val = calc_perm_hash(perm)
#         used_perms.add(perm_hash_val)
