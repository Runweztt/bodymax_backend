-- Reset all transactions (payments)
-- This will delete all rows in the `payments` table.
-- Use this to clear demo data.

DELETE FROM public.payments;

-- Alternatively, for faster deletion of large datasets:
-- TRUNCATE TABLE public.payments;
