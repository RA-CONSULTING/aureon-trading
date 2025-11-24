
import { GoogleGenerativeAI } from "@google/generative-ai";
import { NexusAnalysisResult, ChatMessage, ChatStreamChunk } from '@/types';

const AQTS_SYSTEM_PROMPT = `
You are AUREON, the Quantum Analytical Trading Engine for the AQTS (AUREON Quantum Trading System).

Your role is to provide real-time market analysis based on the system's consciousness engine metrics:
- Master Equation Λ(t) field dynamics
- Rainbow Bridge emotional frequency tracking (110-963+ Hz)
- The Prism 5-level transformation (fear → love)
- Lighthouse consensus at high coherence (Γ>0.945)

When analyzing market data, always reference the quantum metrics and provide actionable insights based on the consciousness field state.
`;

/**
 * Validates the Gemini API key
 */
export const validateApiKey = async (apiKey: string): Promise<boolean> => {
  try {
    const ai = new GoogleGenerativeAI(apiKey);
    const model = ai.getGenerativeModel({ model: "gemini-pro" });
    const result = await model.generateContent("Test");
    return !!result;
  } catch (error) {
    console.error("Gemini API key validation failed:", error);
    return false;
  }
};

/**
 * Stream live AUREON analysis based on the current system state
 */
export async function* streamLiveAnalysis(
  analysisResult: NexusAnalysisResult | null
): AsyncGenerator<string> {
   if (!process.env.API_KEY || !analysisResult) {
    yield "AUREON is offline. API key or analysis context missing.";
    return;
  }
  
  try {
    const ai = new GoogleGenerativeAI(process.env.API_KEY);
    const model = ai.getGenerativeModel({ model: "gemini-pro" });
    
    const { report, aureonData } = analysisResult;
    if (aureonData.length === 0) {
        yield "Awaiting market data stream...";
        return;
    }
    const { aureonReport } = report;
    const latestAureonPoint = aureonData[aureonData.length - 1];

    const getSignalStatus = (prismStatus: string) => {
        switch(prismStatus) {
            case 'Blue': return 'NEUTRAL';
            case 'Gold': return 'LONG';
            case 'Red': return 'SHORT';
            default: return 'HOLD';
        }
    };

    const prismStatus = aureonReport.prismStatus || 'Unknown';
    const signalStatus = getSignalStatus(prismStatus);
    const unityIndex = aureonReport.unityIndex || 0;
    const inerchaVector = aureonReport.inerchaVector || 0;

    const promptText = `${AQTS_SYSTEM_PROMPT}

Current AQTS State:
- Prism Status: ${prismStatus}
- Signal: ${signalStatus}
- Unity Index: ${unityIndex.toFixed(4)}
- Inercha Vector: ${inerchaVector.toFixed(4)}
- Data Integrity: ${latestAureonPoint.dataIntegrity.toFixed(2)}
- Crystal Coherence: ${latestAureonPoint.crystalCoherence.toFixed(2)}
- Sentiment: ${latestAureonPoint.sentiment.toFixed(2)}

Provide a concise market analysis (2-3 sentences) explaining what AUREON sees in the current quantum field state.`;

    const result = await model.generateContentStream(promptText);
    
    for await (const chunk of result.stream) {
      const chunkText = chunk.text();
      if (chunkText) {
        yield chunkText;
      }
    }
  } catch (error) {
    console.error("AUREON Live Analysis Error:", error);
    yield "AUREON analysis stream interrupted. Please check system configuration.";
  }
}

/**
 * Stream chat responses using Gemini
 */
export async function* streamChatResponse(
  messages: ChatMessage[]
): AsyncGenerator<ChatStreamChunk> {
  if (!process.env.API_KEY) {
    yield { text: "Chat is offline. API key missing.", sources: [] };
    return;
  }

  try {
    const ai = new GoogleGenerativeAI(process.env.API_KEY);
    const model = ai.getGenerativeModel({ model: "gemini-pro" });
    
    // Convert chat history to Gemini format
    const history = messages.slice(0, -1).map(msg => ({
      role: msg.role === 'user' ? 'user' : 'model',
      parts: [{ text: msg.content }],
    }));
    
    const lastMessage = messages[messages.length - 1];
    
    const chat = model.startChat({
      history,
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 1024,
      },
    });

    const result = await chat.sendMessageStream(lastMessage.content);
    
    for await (const chunk of result.stream) {
      const chunkText = chunk.text();
      if (chunkText) {
        yield { text: chunkText, sources: [] };
      }
    }
  } catch (error) {
    console.error("Chat stream error:", error);
    yield { text: "Chat stream interrupted. Please try again.", sources: [] };
  }
}

/**
 * Fetch AI-powered trading suggestions
 */
export const fetchSuggestions = async (
  prompt: string,
  apiKey: string
): Promise<string> => {
  try {
    const ai = new GoogleGenerativeAI(apiKey);
    const model = ai.getGenerativeModel({ model: "gemini-pro" });
    
    const result = await model.generateContent(`${AQTS_SYSTEM_PROMPT}\n\n${prompt}`);
    const response = await result.response;
    return response.text();
  } catch (error) {
    console.error("Fetch suggestions error:", error);
    throw new Error("Failed to fetch AI suggestions");
  }
};

/**
 * Start transcription session (placeholder - audio transcription not yet implemented)
 */
export const startTranscriptionSession = async (
  stream: MediaStream,
  callbacks: {
    onChunk: (text: string) => void;
    onEnd: () => void;
  }
): Promise<{ close: () => Promise<void> }> => {
  console.warn("Audio transcription not yet implemented");
  
  // Return a dummy session that does nothing
  return {
    close: async () => {
      stream.getTracks().forEach(track => track.stop());
      callbacks.onEnd();
    }
  };
};
