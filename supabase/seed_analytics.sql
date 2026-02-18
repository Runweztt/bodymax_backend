-- 1. Ensure date columns exist for historical tracking
-- Only run these once! They add the necessary columns to track PAST revenue and attendance.
ALTER TABLE public.payments ADD COLUMN IF NOT EXISTS transaction_date DATE DEFAULT CURRENT_DATE;
ALTER TABLE public.attendance ADD COLUMN IF NOT EXISTS attendance_date DATE DEFAULT CURRENT_DATE;

-- 2. Clear existing sample data to avoid duplicates if preferred (Optional)
-- DELETE FROM public.payments;
-- DELETE FROM public.attendance;

-- 3. Insert Historical Payments for December 2025
-- Using member IDs 1-4 based on your previous seeding
INSERT INTO public.payments (member_id, amount, payment_method, transaction_date)
VALUES 
(1, 30000, 'Mobile Money', '2025-12-05'),
(2, 30000, 'Cash', '2025-12-10'),
(3, 20000, 'Mobile Money', '2025-12-15'),
(4, 30000, 'Cash', '2025-12-20'),
(1, 15000, 'Mobile Money', '2025-12-28');

-- 4. Insert Historical Payments for January 2026
INSERT INTO public.payments (member_id, amount, payment_method, transaction_date)
VALUES 
(1, 30000, 'Mobile Money', '2026-01-05'),
(2, 30000, 'Cash', '2026-01-08'),
(3, 20000, 'Mobile Money', '2026-01-12'),
(4, 30000, 'Cash', '2026-01-15'),
(2, 5000, 'Cash', '2026-01-19'),
(1, 30000, 'Mobile Money', '2026-01-20');

-- 5. Insert Historical Attendance Records
INSERT INTO public.attendance (member_id, attendance_date)
VALUES
(1, '2025-12-01'), (2, '2025-12-02'), (3, '2025-12-03'), (4, '2025-12-04'),
(1, '2025-12-15'), (2, '2025-12-16'), (3, '2025-12-17'), (4, '2025-12-18'),
(1, '2026-01-02'), (2, '2026-01-03'), (3, '2026-01-04'), (4, '2026-01-05'),
(1, '2026-01-15'), (2, '2026-01-16'), (3, '2026-01-17'), (4, '2026-01-18');
