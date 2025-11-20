-- Extend profiles table for KYC compliance
ALTER TABLE public.profiles
ADD COLUMN date_of_birth DATE,
ADD COLUMN location TEXT,
ADD COLUMN id_document_path TEXT,
ADD COLUMN kyc_status TEXT DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'verified', 'rejected')),
ADD COLUMN kyc_verified_at TIMESTAMPTZ,
ADD COLUMN data_consent_given BOOLEAN DEFAULT false,
ADD COLUMN data_consent_date TIMESTAMPTZ;

-- Create user_binance_credentials table for encrypted API credentials
CREATE TABLE public.user_binance_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
  api_key_encrypted TEXT NOT NULL,
  api_secret_encrypted TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  last_used_at TIMESTAMPTZ
);

-- Enable RLS on user_binance_credentials
ALTER TABLE public.user_binance_credentials ENABLE ROW LEVEL SECURITY;

-- Users can only read their own credentials
CREATE POLICY "Users can view own credentials"
ON public.user_binance_credentials
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Users can insert their own credentials
CREATE POLICY "Users can insert own credentials"
ON public.user_binance_credentials
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can update their own credentials
CREATE POLICY "Users can update own credentials"
ON public.user_binance_credentials
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);

-- Create audit log for compliance
CREATE TABLE public.data_access_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  accessed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  access_type TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  ip_address TEXT,
  timestamp TIMESTAMPTZ DEFAULT now() NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable RLS on audit log
ALTER TABLE public.data_access_audit ENABLE ROW LEVEL SECURITY;

-- Only admins can read audit logs
CREATE POLICY "Admins can read audit logs"
ON public.data_access_audit
FOR SELECT
TO authenticated
USING (has_role(auth.uid(), 'admin'));

-- Service role can insert audit logs
CREATE POLICY "Service can insert audit logs"
ON public.data_access_audit
FOR INSERT
WITH CHECK (true);

-- Create storage bucket for ID documents
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'id-verification',
  'id-verification',
  false,
  5242880, -- 5MB limit
  ARRAY['image/jpeg', 'image/png', 'application/pdf']
);

-- Storage policies for ID documents
CREATE POLICY "Users can upload own ID documents"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'id-verification' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can view own ID documents"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'id-verification' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Admins can view all ID documents"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'id-verification' 
  AND has_role(auth.uid(), 'admin')
);

-- Update trigger for user_binance_credentials
CREATE TRIGGER update_binance_credentials_updated_at
BEFORE UPDATE ON public.user_binance_credentials
FOR EACH ROW
EXECUTE FUNCTION public.handle_updated_at();