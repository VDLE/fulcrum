-- Reference / lookup data required for the application to function.
-- Loaded automatically on first DB init via docker-entrypoint-initdb.d.
-- Safe to re-run: every block uses INSERT IGNORE so repeated loads don't error.

INSERT IGNORE INTO role_type (role_type_name, role_type_description) VALUES
    ('Researcher', 'Making and running studies'),
    ('Facilitator', 'Managing researchers');

INSERT IGNORE INTO study_design_type (study_design_type_id, study_design_type_description) VALUES
    (1, 'Within'),
    (2, 'Between');

INSERT IGNORE INTO study_user_access_type (study_user_access_type_id, study_user_access_type_description) VALUES
    (1, 'Read'),
    (2, 'Read/Write');

INSERT IGNORE INTO study_user_role_type (study_user_role_type_id, study_user_role_description, study_user_access_type_id) VALUES
    (1, 'Owner', 2),
    (2, 'Viewer', 1),
    (3, 'Editor', 2);

INSERT IGNORE INTO measurement_option (measurement_option_id, measurement_option_name) VALUES
    (1, 'Mouse Movement'),
    (2, 'Mouse Scrolls'),
    (3, 'Mouse Clicks'),
    (4, 'Keyboard Inputs'),
    (5, 'Screen Recording'),
    (6, 'Heat Map');

INSERT IGNORE INTO gender_type (gender_description) VALUES
    ('Male'),
    ('Female'),
    ('Non-Binary'),
    ('Other'),
    ('Prefer Not to Say');

INSERT IGNORE INTO ethnicity_type (ethnicity_description) VALUES
    ('American Indian or Alaska Native'),
    ('Asian'),
    ('Black or African American'),
    ('Hispanic or Latino'),
    ('Native Hawaiian or Other Pacific Islander'),
    ('White');

INSERT IGNORE INTO highest_education_type (highest_education_description) VALUES
    ('Some High School'),
    ('High School Graduate or Equivalent'),
    ('Some College'),
    ('Associate''s Degree'),
    ('Bachelor''s Degree'),
    ('Master''s Degree'),
    ('Doctorate');
