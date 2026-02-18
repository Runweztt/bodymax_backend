-- 1. Reset Schema (Careful! This deletes data)
drop table if exists public.payments cascade;
drop table if exists public.attendance cascade;
drop table if exists public.members cascade;
drop table if exists public.trainers cascade;
drop table if exists public.profiles cascade;

-- 2. Create Tables
-- Members Table
create table public.members (

    id uuid default uuid_generate_v4() primary key,
    full_name text not null,
    phone text,
    email text,
    category text not null check (category in ('Group Membership', 'Normal Membership', 'Daily Pass')),
    duration text check (duration in ('Weekly', 'Monthly', '3 Months', 'Annual')),
    start_date date not null default current_date,
    expiry_date date not null,
    status text not null default 'Active' check (status in ('Active', 'Expiring Soon', 'Expired')),
    group_id uuid, -- For Group Membership linking
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Attendance Table
create table public.attendance (
    id uuid default uuid_generate_v4() primary key,
    member_id uuid references public.members(id) on delete cascade not null,
    check_in_time timestamp with time zone default timezone('utc'::text, now()) not null,
    attendance_date date not null default current_date
);

-- 3. Payments Table
create table public.payments (
    id uuid default uuid_generate_v4() primary key,
    member_id uuid references public.members(id) on delete cascade not null,
    amount decimal(12,2) not null,
    payment_method text not null check (payment_method in ('Cash', 'Mobile Money')),
    transaction_date timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 4. Trainers Table
create table public.trainers (
    id uuid default uuid_generate_v4() primary key,
    name text not null,
    specialty text,
    schedule jsonb, -- Weekly schedule storage
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 5. Role Table (Simple RBAC metadata)
create table public.profiles (
  id uuid references auth.users on delete cascade primary key,
  role text not null check (role in ('Receptionist', 'Manager')) default 'Receptionist'
);

-- RLS (Row Level Security) - Simplified for brevity
alter table public.members enable row level security;
alter table public.attendance enable row level security;
alter table public.payments enable row level security;
alter table public.trainers enable row level security;
alter table public.profiles enable row level security;

-- Policies (Example: Authenticated users can read)
create policy "Authenticated users can view members" on public.members for select to authenticated using (true);
create policy "Authenticated users can mark attendance" on public.attendance for insert to authenticated with check (true);
create policy "Managers can view all payments" on public.payments for all to authenticated using (
  exists (select 1 from public.profiles where id = auth.uid() and role = 'Manager')
);

-- Idempotency Constraints
create unique index idx_members_phone on public.members (phone) where phone is not null;
create unique index idx_members_email on public.members (email) where email is not null;
alter table public.attendance add constraint uq_attendance_member_date unique (member_id, attendance_date);
