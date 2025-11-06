-- ================================================
-- Supabase Real-time Notifications Setup
-- ================================================
-- This script creates the notifications table in Supabase
-- with Row Level Security (RLS) and real-time capabilities
-- ================================================

-- Create notifications table
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    username TEXT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Link to related object (optional)
    related_model TEXT,
    related_id TEXT,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Django sync
    django_id INTEGER UNIQUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON public.notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON public.notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON public.notifications(user_id, is_read) WHERE is_read = FALSE;

-- Enable Row Level Security
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Users can insert own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Users can update own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Users can delete own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Service role can do anything" ON public.notifications;

-- RLS Policies: Users can only see their own notifications
CREATE POLICY "Users can view own notifications"
    ON public.notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own notifications"
    ON public.notifications FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications"
    ON public.notifications FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own notifications"
    ON public.notifications FOR DELETE
    USING (auth.uid() = user_id);

-- Allow service role to bypass RLS for backend operations
CREATE POLICY "Service role can do anything"
    ON public.notifications FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_notifications_updated_at ON public.notifications;
CREATE TRIGGER update_notifications_updated_at
    BEFORE UPDATE ON public.notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable realtime for notifications table
ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;

-- ================================================
-- IMPORTANT: To enable real-time in Supabase Dashboard:
-- ================================================
-- 1. Go to Database > Replication in Supabase Dashboard
-- 2. Enable replication for 'notifications' table
-- 3. Select all events: INSERT, UPDATE, DELETE
-- ================================================

-- Grant permissions
GRANT ALL ON public.notifications TO authenticated;
GRANT ALL ON public.notifications TO service_role;

-- ================================================
-- Test queries (optional)
-- ================================================
-- Create a test notification:
-- INSERT INTO public.notifications (user_id, username, title, message, notification_type)
-- VALUES (auth.uid(), 'test_user', 'Test Notification', 'This is a test message', 'info');

-- Get unread notifications count:
-- SELECT COUNT(*) FROM public.notifications WHERE user_id = auth.uid() AND is_read = FALSE;

-- Mark all as read:
-- UPDATE public.notifications SET is_read = TRUE, read_at = NOW() WHERE user_id = auth.uid() AND is_read = FALSE;
