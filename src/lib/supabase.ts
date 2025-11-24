import { createClient } from '@supabase/supabase-js';


// Initialize Supabase client
// Using direct values from project configuration
const supabaseUrl = 'https://siihxcwetdjdsrfdexmb.supabase.co';
const supabaseKey = 'sb_publishable_F5efTQEGXIBE8kg5VCGhkg_4prlajr2';
const supabase = createClient(supabaseUrl, supabaseKey);


export { supabase };