import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import AureonDashboard from '@/components/AureonDashboard';
import PaymentGate from '@/components/PaymentGate';

const SUPER_USER_EMAIL = "gary@raconsultingandbrokerageservices.com";

export default function Index() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [paymentComplete, setPaymentComplete] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setUserId(session.user.id);
        checkPaymentStatus(session.user.id, session.user.email);
      } else {
        setAuthenticated(false);
        setLoading(false);
        navigate('/auth');
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUserId(session.user.id);
        checkPaymentStatus(session.user.id, session.user.email);
      } else {
        setLoading(false);
        navigate('/auth');
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  const checkPaymentStatus = async (uid: string, email: string | undefined) => {
    setAuthenticated(true);
    
    // Super user bypasses payment
    if (email === SUPER_USER_EMAIL) {
      setPaymentComplete(true);
      setLoading(false);
      return;
    }

    const { data } = await supabase
      .from('aureon_user_sessions')
      .select('payment_completed')
      .eq('user_id', uid)
      .single();

    setPaymentComplete(data?.payment_completed || false);
    setLoading(false);
  };

  const handlePaymentComplete = async () => {
    if (!userId) return;
    
    await supabase
      .from('aureon_user_sessions')
      .update({ 
        payment_completed: true,
        payment_completed_at: new Date().toISOString()
      })
      .eq('user_id', userId);
    
    setPaymentComplete(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!authenticated) {
    return null; // Will redirect to /auth
  }

  if (!paymentComplete && userId) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <PaymentGate userId={userId} onPaymentComplete={handlePaymentComplete} />
      </div>
    );
  }

  return <AureonDashboard />;
}