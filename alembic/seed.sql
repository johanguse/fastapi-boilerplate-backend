-- seed.sql

-- Insert Users
INSERT INTO users (email, name, hashed_password, is_active, is_superuser, is_verified, role)
VALUES 
    ('admin@example.com', 'Admin User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGpfUF/Hp/i', true, true, true, 'admin'),
    ('user@example.com', 'Regular User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGpfUF/Hp/i', true, false, true, 'member');

-- Insert Teams
INSERT INTO teams (name, plan_name, subscription_status)
VALUES 
    ('Development Team', 'pro', 'active'),
    ('Marketing Team', 'basic', 'active');

-- Insert Projects
INSERT INTO projects (name, description, team_id)
VALUES 
    ('Website Redesign', 'Complete overhaul of company website', 1),
    ('Marketing Campaign', 'Q2 Marketing Campaign', 2);

-- Insert Team Members (linking users to teams)
INSERT INTO team_members (user_id, team_id, role)
VALUES 
    (1, 1, 'admin'),  -- Admin user in Development Team
    (2, 2, 'member'); -- Regular user in Marketing Team

-- Insert Blog Posts
INSERT INTO blog_posts (title, content, user_id)
VALUES 
    ('Welcome to Our Blog', 'This is our first blog post...', 1),
    ('Getting Started Guide', 'Here''s how to get started...', 1);

-- Insert Activity Logs
INSERT INTO activity_logs (project_id, user_id, team_id, action, ip_address)
VALUES 
    (1, 1, 1, 'Project created', '127.0.0.1'),
    (2, 2, 2, 'Project created', '127.0.0.1');

-- Insert Invitations
INSERT INTO invitations (team_id, email, role, invited_by_id, status)
VALUES 
    (1, 'newdev@example.com', 'member', 1, 'pending'),
    (2, 'newmarketer@example.com', 'member', 2, 'pending');