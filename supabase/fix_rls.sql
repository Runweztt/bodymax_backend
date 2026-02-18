
-- Fix missing RLS policies for BodyMax Gym (Idempotent Version)

-- 1. Profiles: Users need to be able to read their own profile to determine their role
drop policy if exists "Users can view their own profile" on public.profiles;
create policy "Users can view their own profile" on public.profiles for select to authenticated using (auth.uid() = id);

-- 2. Attendance: Authenticated users need to manage daily attendance
drop policy if exists "Authenticated users can view attendance" on public.attendance;
drop policy if exists "Authenticated users can manage attendance" on public.attendance;
create policy "Authenticated users can manage attendance" on public.attendance for all to authenticated using (true);

-- 3. Payments: Allow all actions for managers/receptionists for now to enable enrollment
drop policy if exists "Managers can view all payments" on public.payments;
drop policy if exists "Authenticated users can view payments" on public.payments;
drop policy if exists "Authenticated users can manage payments" on public.payments;
create policy "Authenticated users can manage payments" on public.payments for all to authenticated using (true);

-- 4. Members: Allow view and insertion
drop policy if exists "Authenticated users can view members" on public.members;
drop policy if exists "Authenticated users can manage members" on public.members;
create policy "Authenticated users can manage members" on public.members for all to authenticated using (true);

-- 5. Trainers: Commented out because table might not exist yet
-- drop policy if exists "Authenticated users can view trainers" on public.trainers;
-- create policy "Authenticated users can view trainers" on public.trainers for select to authenticated using (true);
