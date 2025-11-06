-- ============================================================================
-- Supabase Storage Bucket Setup for File Uploads
-- Run this in Supabase Dashboard > SQL Editor
-- ============================================================================

-- Create storage bucket for user files
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-files', 'user-files', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for user-files bucket
-- Policy 1: Users can upload their own files
CREATE POLICY "Users can upload own files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'user-files'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy 2: Users can view their own files
CREATE POLICY "Users can view own files"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'user-files'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy 3: Users can update their own files
CREATE POLICY "Users can update own files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'user-files'
  AND auth.uid()::text = (storage.foldername(name))[1]
)
WITH CHECK (
  bucket_id = 'user-files'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy 4: Users can delete their own files
CREATE POLICY "Users can delete own files"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'user-files'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Create public bucket for public assets (optional)
INSERT INTO storage.buckets (id, name, public)
VALUES ('public-assets', 'public-assets', true)
ON CONFLICT (id) DO NOTHING;

-- Policy for public assets - anyone can view
CREATE POLICY "Public assets are viewable by everyone"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'public-assets');

-- Policy for authenticated users to upload to public assets
CREATE POLICY "Authenticated users can upload public assets"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'public-assets');

-- ============================================================================
-- File metadata table (optional - tracks uploads in database)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.uploaded_files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  file_size BIGINT NOT NULL,
  mime_type TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  bucket_id TEXT NOT NULL DEFAULT 'user-files',
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.uploaded_files ENABLE ROW LEVEL SECURITY;

-- RLS Policies for uploaded_files table
CREATE POLICY "Users can view own uploaded files"
ON public.uploaded_files
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own uploaded files"
ON public.uploaded_files
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own uploaded files"
ON public.uploaded_files
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own uploaded files"
ON public.uploaded_files
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_uploaded_files_user_id
ON public.uploaded_files(user_id);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_created_at
ON public.uploaded_files(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_uploaded_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_uploaded_files_updated_at
BEFORE UPDATE ON public.uploaded_files
FOR EACH ROW
EXECUTE FUNCTION public.update_uploaded_files_updated_at();

-- ============================================================================
-- Verification queries
-- ============================================================================

-- Check buckets
SELECT * FROM storage.buckets;

-- Check policies
SELECT * FROM pg_policies WHERE tablename = 'objects';

-- Check uploaded_files table
SELECT * FROM public.uploaded_files;
