import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { Resend } from "npm:resend@4.0.0";

const resend = new Resend(Deno.env.get("RESEND_API_KEY"));

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface SignupNotificationRequest {
  email: string;
  fullName?: string;
  location?: string;
  dateOfBirth?: string;
}

const handler = async (req: Request): Promise<Response> => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { email, fullName, location, dateOfBirth }: SignupNotificationRequest = await req.json();

    console.log('[send-signup-notification] Processing signup notification for:', email);

    const emailResponse = await resend.emails.send({
      from: "AUREON Trading <onboarding@resend.dev>",
      to: ["gary@raconsultingandbrokerageservices.com"],
      subject: "🎉 New User Signup - AUREON Trading Platform",
      html: `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
              }
              .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 8px 8px 0 0;
                text-align: center;
              }
              .header h1 {
                margin: 0;
                font-size: 24px;
              }
              .content {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 8px 8px;
              }
              .info-box {
                background: white;
                padding: 20px;
                border-radius: 6px;
                margin: 20px 0;
                border-left: 4px solid #667eea;
              }
              .info-row {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e9ecef;
              }
              .info-row:last-child {
                border-bottom: none;
              }
              .label {
                font-weight: 600;
                color: #6c757d;
              }
              .value {
                color: #212529;
              }
              .timestamp {
                text-align: center;
                color: #6c757d;
                font-size: 14px;
                margin-top: 20px;
              }
              .footer {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
                font-size: 12px;
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>🌈 New User Registration</h1>
              <p style="margin: 10px 0 0 0;">AUREON Quantum Trading System</p>
            </div>
            <div class="content">
              <p>A new user has signed up for the AUREON Trading Platform.</p>
              
              <div class="info-box">
                <h2 style="margin-top: 0; font-size: 18px; color: #667eea;">User Details</h2>
                
                <div class="info-row">
                  <span class="label">Email:</span>
                  <span class="value">${email}</span>
                </div>
                
                ${fullName ? `
                <div class="info-row">
                  <span class="label">Full Name:</span>
                  <span class="value">${fullName}</span>
                </div>
                ` : ''}
                
                ${location ? `
                <div class="info-row">
                  <span class="label">Location:</span>
                  <span class="value">${location}</span>
                </div>
                ` : ''}
                
                ${dateOfBirth ? `
                <div class="info-row">
                  <span class="label">Date of Birth:</span>
                  <span class="value">${new Date(dateOfBirth).toLocaleDateString()}</span>
                </div>
                ` : ''}
                
                <div class="info-row">
                  <span class="label">KYC Status:</span>
                  <span class="value" style="color: #ffc107;">⏳ Pending Review</span>
                </div>
              </div>
              
              <p style="background: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <strong>Action Required:</strong> Please review the KYC application in the admin dashboard.
              </p>
              
              <div class="timestamp">
                Registration Time: ${new Date().toLocaleString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric', 
                  hour: '2-digit', 
                  minute: '2-digit',
                  timeZoneName: 'short'
                })}
              </div>
            </div>
            
            <div class="footer">
              <p>AUREON Quantum Trading System</p>
              <p>The Prism That Turns Fear Into Love 💚</p>
              <p style="margin-top: 10px; font-size: 11px;">777-ixz1470 → RAINBOW BRIDGE → PRISM → 528 Hz</p>
            </div>
          </body>
        </html>
      `,
    });

    console.log('[send-signup-notification] Email sent successfully:', emailResponse);

    return new Response(JSON.stringify({ success: true, emailResponse }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        ...corsHeaders,
      },
    });
  } catch (error: any) {
    console.error('[send-signup-notification] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      }
    );
  }
};

serve(handler);
