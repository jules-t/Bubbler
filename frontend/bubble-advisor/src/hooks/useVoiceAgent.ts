import { useState, useRef, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/api/client';
import { ConversationResponse } from '@/types/api';

export const useVoiceAgent = (bubbleId: string) => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [lastTranscript, setLastTranscript] = useState<string>("");
  const [lastResponse, setLastResponse] = useState<string>("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const { toast } = useToast();

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsListening(true);
      
      toast({
        title: "Listening...",
        description: "Speak your instructions to adjust the bubble",
      });
    } catch (error) {
      console.error('Error starting recording:', error);
      toast({
        title: "Microphone Error",
        description: "Unable to access microphone. Please check permissions.",
        variant: "destructive",
      });
    }
  }, [toast]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsListening(false);
      setIsProcessing(true);
    }
  }, []);

  const processAudio = async (audioBlob: Blob) => {
    try {
      // Convert audio blob to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);

      return new Promise((resolve, reject) => {
        reader.onloadend = async () => {
          try {
            const base64Audio = (reader.result as string).split(',')[1];

            toast({
              title: "Processing...",
              description: "Sending your voice to the bubble...",
            });

            // Call backend API
            const response: ConversationResponse = await apiClient.sendVoiceMessage(
              bubbleId,
              base64Audio,
              conversationId
            );

            // Store conversation ID for context
            setConversationId(response.conversation_id);
            setLastTranscript(response.user_transcript);
            setLastResponse(response.bubble_response);

            // Play the audio response
            const audioResponseBlob = base64ToBlob(response.audio_base64, 'audio/mpeg');
            const audioUrl = URL.createObjectURL(audioResponseBlob);
            const audio = new Audio(audioUrl);

            audio.onended = () => {
              URL.revokeObjectURL(audioUrl);
            };

            await audio.play();

            toast({
              title: "Bubble responded",
              description: response.bubble_response,
            });

            setIsProcessing(false);
            resolve(response);
          } catch (error) {
            console.error('Error processing audio:', error);

            // Better error message extraction
            let errorMessage = "Failed to process your voice input";

            if (error instanceof Error) {
              errorMessage = error.message;
            } else if (typeof error === 'object' && error !== null) {
              // Handle various error object structures
              errorMessage = (error as any).detail ||
                             (error as any).message ||
                             JSON.stringify(error);
            } else if (typeof error === 'string') {
              errorMessage = error;
            }

            toast({
              title: "Processing Error",
              description: errorMessage,
              variant: "destructive",
            });
            setIsProcessing(false);
            reject(error);
          }
        };
      });
    } catch (error) {
      console.error('Error in processAudio:', error);

      // Better error message extraction
      let errorMessage = "Failed to process your voice input";

      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null) {
        errorMessage = (error as any).detail ||
                       (error as any).message ||
                       JSON.stringify(error);
      } else if (typeof error === 'string') {
        errorMessage = error;
      }

      toast({
        title: "Processing Error",
        description: errorMessage,
        variant: "destructive",
      });

      setIsProcessing(false);
      throw error;
    }
  };

  const base64ToBlob = (base64: string, mimeType: string): Blob => {
    const byteCharacters = atob(base64);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += 512) {
      const slice = byteCharacters.slice(offset, offset + 512);
      const byteNumbers = new Array(slice.length);

      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }

      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }

    return new Blob(byteArrays, { type: mimeType });
  };

  return {
    isListening,
    isProcessing,
    startRecording,
    stopRecording,
    lastTranscript,
    lastResponse,
    conversationId,
  };
};
