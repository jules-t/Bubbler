import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff } from "lucide-react";
import { Button } from "@/components/ui/button";

interface BubbleVisualizationProps {
  score: number;
  title: string;
  subtitle: string;
  isUserBubble?: boolean;
  onVoiceStart?: () => void;
  onVoiceStop?: () => void;
  isListening?: boolean;
}

export const BubbleVisualization = ({
  score,
  title,
  subtitle,
  isUserBubble = false,
  onVoiceStart,
  onVoiceStop,
  isListening = false,
}: BubbleVisualizationProps) => {
  const [prevScore, setPrevScore] = useState(score);
  const [animation, setAnimation] = useState<"pulse" | "inflate" | "shrink" | "burst" | null>("pulse");

  useEffect(() => {
    if (score !== prevScore) {
      const diff = Math.abs(score - prevScore);
      if (score > prevScore && diff > 5) {
        setAnimation("inflate");
      } else if (score < prevScore && diff > 5) {
        setAnimation("shrink");
      } else if (score > 85) {
        setAnimation("burst");
      } else {
        setAnimation("pulse");
      }
      setPrevScore(score);
    }
  }, [score, prevScore]);

  const getBurstRisk = (score: number) => {
    if (score >= 85) return { label: "CRITICAL", color: "text-bubble-danger" };
    if (score >= 70) return { label: "HIGH", color: "text-bubble-warning" };
    if (score >= 50) return { label: "MODERATE", color: "text-yellow-500" };
    return { label: "LOW", color: "text-bubble-success" };
  };

  const getTimeEstimate = (score: number) => {
    if (score >= 90) return "< 14 days";
    if (score >= 85) return "1-2 months";
    if (score >= 75) return "2-4 months";
    if (score >= 65) return "4-8 months";
    if (score >= 50) return "8-18 months";
    if (score >= 35) return "18-36 months";
    return "3+ years";
  };

  const risk = getBurstRisk(score);
  // Dramatic bubble size scaling for clear visual feedback
  // Min size: 80px at score 0, Max size: 500px at score 100
  const bubbleSize = 130 + score * 3.3;

  return (
    <div className="relative flex flex-col items-center justify-between h-full p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-primary mb-2">{title}</h2>
        <p className="text-muted-foreground text-sm">{subtitle}</p>
      </div>

      <div className="flex-1 flex items-center justify-center relative">
        {/* Voice control button */}
        {isUserBubble && onVoiceStart && onVoiceStop && (
          <motion.div
            className="absolute top-0 right-0 z-10"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Button
              onClick={isListening ? onVoiceStop : onVoiceStart}
              variant={isListening ? "default" : "outline"}
              size="icon"
              className={`rounded-full ${isListening ? "animate-pulse" : ""}`}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </Button>
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={score}
            className="relative cursor-pointer"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{
              scale: 1,
              opacity: 1,
              ...(animation === "pulse" && {
                scale: [1, 1.02, 1],
              }),
              ...(animation === "inflate" && {
                scale: [0.9, 1.1, 1],
              }),
              ...(animation === "shrink" && {
                scale: [1, 0.9, 1],
              }),
            }}
            transition={{
              duration: animation === "pulse" ? 2 : 0.6,
              repeat: animation === "pulse" ? Infinity : 0,
              ease: "easeInOut",
            }}
            style={{
              width: bubbleSize,
              height: bubbleSize,
            }}
            onClick={isUserBubble && !isListening ? onVoiceStart : undefined}
          >
            {/* Outer glow effect */}
            <motion.div
              className="absolute inset-0 rounded-full bubble-glow-strong"
              animate={{
                scale: [1, 1.08, 1],
                opacity: [0.6, 0.8, 0.6],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            {/* Main bubble with gradient */}
            <div
              className="absolute inset-0 rounded-full border-2 border-primary/20 backdrop-blur-md overflow-hidden"
              style={{
                background: `radial-gradient(circle at 30% 30%, 
                  hsl(var(--bubble-glow) / 0.35) 0%, 
                  hsl(var(--bubble-primary) / 0.25) 30%,
                  hsl(var(--bubble-secondary) / 0.15) 60%, 
                  hsl(var(--bubble-primary) / 0.08) 100%)`,
              }}
            >
              {/* Primary highlight */}
              <motion.div
                className="absolute top-6 left-6 w-20 h-20 rounded-full"
                style={{
                  background: `radial-gradient(circle, 
                    rgba(255, 255, 255, 0.5) 0%, 
                    rgba(255, 255, 255, 0.2) 40%,
                    transparent 70%)`,
                }}
                animate={{
                  scale: [1, 1.1, 1],
                  opacity: [0.6, 0.8, 0.6],
                }}
                transition={{
                  duration: 2.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />

              {/* Secondary highlight */}
              <motion.div
                className="absolute bottom-12 right-12 w-12 h-12 rounded-full"
                style={{
                  background: `radial-gradient(circle, 
                    rgba(255, 255, 255, 0.3) 0%, 
                    transparent 60%)`,
                }}
                animate={{
                  scale: [1, 1.15, 1],
                  opacity: [0.4, 0.6, 0.4],
                }}
                transition={{
                  duration: 3.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 0.5,
                }}
              />

              {/* Floating particles */}
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute rounded-full bg-primary/30"
                  style={{
                    width: `${4 + i * 2}px`,
                    height: `${4 + i * 2}px`,
                    top: `${15 + i * 18}%`,
                    left: `${55 + i * 8}%`,
                  }}
                  animate={{
                    y: [-15, 15, -15],
                    x: [-8, 8, -8],
                    opacity: [0.3, 0.7, 0.3],
                    scale: [1, 1.2, 1],
                  }}
                  transition={{
                    duration: 3.5 + i * 0.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: i * 0.3,
                  }}
                />
              ))}

              {/* Score display */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <motion.div
                  className="text-6xl font-bold bg-gradient-to-br from-primary to-bubble-secondary bg-clip-text text-transparent"
                  animate={{
                    scale: [1, 1.03, 1],
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {Math.round(score)}
                </motion.div>
                <motion.div
                  className="text-xs text-foreground/60 uppercase tracking-wider mt-2 font-medium"
                  animate={{ opacity: [0.6, 1, 0.6] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  Bubble Index
                </motion.div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="w-full space-y-3 mt-8">
        <div className="flex justify-between items-center py-2 border-b border-border/50">
          <span className="text-muted-foreground text-sm font-medium">Bubble Score:</span>
          <span className="text-2xl font-bold text-primary">{score.toFixed(1)}</span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-border/50">
          <span className="text-muted-foreground text-sm font-medium">Burst Risk:</span>
          <span className={`text-lg font-bold ${risk.color}`}>{risk.label}</span>
        </div>
        <div className="flex justify-between items-center py-2">
          <span className="text-muted-foreground text-sm font-medium">Est. Time to Burst:</span>
          <span className="text-base font-semibold text-foreground">{getTimeEstimate(score)}</span>
        </div>
      </div>
    </div>
  );
};
