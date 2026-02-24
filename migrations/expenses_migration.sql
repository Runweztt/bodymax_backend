-- Migration to add expenses table
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    category TEXT NOT NULL, -- e.g., 'Maintenance', 'Supplies', 'Utilities', 'Equipment'
    branch_id UUID REFERENCES branches(id) NOT NULL,
    recorded_by UUID REFERENCES profiles(id) NOT NULL,
    date DATE DEFAULT CURRENT_DATE
);

-- Index for faster filtering by branch and date
CREATE INDEX idx_expenses_branch_id ON expenses(branch_id);
CREATE INDEX idx_expenses_date ON expenses(date);
