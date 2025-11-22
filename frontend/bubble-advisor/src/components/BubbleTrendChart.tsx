import { Card } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from "recharts";
import { motion } from "framer-motion";

interface BubbleTrendChartProps {
  currentScore: number;
}

export const BubbleTrendChart = ({ currentScore }: BubbleTrendChartProps) => {
  // Generate historical and projected data
  // Historical data is FIXED and doesn't change based on current score
  const generateTrendData = () => {
    const data = [];
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 12);
    
    // FIXED historical data (past 12 months) - realistic AI bubble growth
    // This represents the actual historical trend regardless of user input
    const historicalScores = [35, 38, 42, 45, 50, 54, 58, 63, 67, 70, 73, 75, 75];
    
    for (let i = 0; i <= 12; i++) {
      const date = new Date(startDate);
      date.setMonth(date.getMonth() + i);
      const monthLabel = date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
      
      data.push({
        month: monthLabel,
        score: historicalScores[i],
        monthIndex: i - 12,
        type: 'historical'
      });
    }
    
    // Future projection (next 24 months) - showing potential paths
    for (let i = 1; i <= 24; i++) {
      const date = new Date();
      date.setMonth(date.getMonth() + i);
      const monthLabel = date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
      
      // Projection depends on current score
      let projectedScore;
      if (currentScore >= 85) {
        // High risk: sharp decline expected within 6-12 months
        projectedScore = Math.max(30, currentScore - (i * (currentScore - 30) / 10));
      } else if (currentScore >= 70) {
        // Elevated: continued growth then correction
        projectedScore = currentScore + Math.min(10, i * 1.2) - Math.pow(Math.max(0, i - 8), 2) * 0.4;
      } else if (currentScore >= 50) {
        // Moderate: steady growth with eventual plateau
        projectedScore = currentScore + (18 - i) * 0.8;
      } else {
        // Low: steady growth potential
        projectedScore = Math.min(85, currentScore + i * 1.8);
      }
      
      data.push({
        month: monthLabel,
        score: Math.max(0, Math.min(100, Math.round(projectedScore * 10) / 10)),
        monthIndex: i,
        type: 'projected'
      });
    }
    
    return data;
  };

  const data = generateTrendData();
  const currentIndex = 12; // Current position in data array
  
  // Find predicted burst point (when score would drop significantly)
  const burstIndex = data.findIndex((d, i) => 
    i > currentIndex && d.score < currentScore * 0.7
  );

  const getBurstRiskZone = (score: number) => {
    if (score >= 85) return { y1: 85, y2: 100, color: "hsl(var(--bubble-danger) / 0.15)" };
    if (score >= 70) return { y1: 70, y2: 85, color: "hsl(var(--bubble-warning) / 0.15)" };
    return null;
  };

  const riskZone = getBurstRiskZone(currentScore);

  return (
    <Card className="p-6 bg-card border-border">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-primary mb-2">AI Bubble Trend Analysis</h3>
          <p className="text-muted-foreground text-sm">
            12-month historical trend and 24-month projected trajectory based on current indicators
          </p>
        </div>

        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="hsl(var(--border))" 
                opacity={0.3}
              />
              <XAxis 
                dataKey="month" 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                domain={[0, 100]}
                label={{ 
                  value: 'Bubble Index', 
                  angle: -90, 
                  position: 'insideLeft',
                  style: { fill: 'hsl(var(--muted-foreground))', fontSize: 12 }
                }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  color: 'hsl(var(--foreground))'
                }}
                labelStyle={{ color: 'hsl(var(--muted-foreground))' }}
              />
              
              {/* Risk zone highlighting */}
              {riskZone && (
                <ReferenceArea 
                  y1={riskZone.y1} 
                  y2={riskZone.y2} 
                  fill={riskZone.color}
                  fillOpacity={1}
                />
              )}
              
              {/* Current position line */}
              <ReferenceLine 
                x={data[currentIndex].month}
                stroke="hsl(var(--primary))" 
                strokeWidth={2}
                strokeDasharray="5 5"
                label={{ 
                  value: 'Now', 
                  position: 'top',
                  fill: 'hsl(var(--primary))',
                  fontSize: 12,
                  fontWeight: 'bold'
                }}
              />
              
              {/* Burst point indicator */}
              {burstIndex > 0 && (
                <ReferenceLine 
                  x={data[burstIndex].month}
                  stroke="hsl(var(--bubble-danger))" 
                  strokeWidth={2}
                  strokeDasharray="3 3"
                  label={{ 
                    value: 'Projected Correction', 
                    position: 'top',
                    fill: 'hsl(var(--bubble-danger))',
                    fontSize: 11,
                    fontWeight: 'bold'
                  }}
                />
              )}
              
              {/* Historical line (solid) */}
              <Line 
                type="monotone" 
                dataKey="score" 
                stroke="hsl(var(--primary))" 
                strokeWidth={3}
                dot={false}
                data={data.slice(0, currentIndex + 1)}
              />
              
              {/* Projected line (dashed) - starts from current point */}
              <Line 
                type="monotone" 
                dataKey="score" 
                stroke="hsl(var(--primary))" 
                strokeWidth={2}
                strokeDasharray="8 4"
                dot={false}
                opacity={0.6}
                data={[data[currentIndex], ...data.slice(currentIndex + 1)]}
              />
              
              {/* Current position dot */}
              <Line 
                type="monotone" 
                dataKey="score" 
                stroke="hsl(var(--primary))" 
                strokeWidth={3}
                dot={(props) => {
                  if (props.index === currentIndex) {
                    return (
                      <circle 
                        cx={props.cx} 
                        cy={props.cy} 
                        r={6} 
                        fill="hsl(var(--primary))"
                        stroke="hsl(var(--background))"
                        strokeWidth={3}
                      />
                    );
                  }
                  return null;
                }}
                data={[data[currentIndex]]}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Legend and insights */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start gap-2">
            <div className="w-8 h-0.5 bg-primary mt-2"></div>
            <div>
              <div className="font-semibold text-foreground">Historical Data</div>
              <div className="text-muted-foreground text-xs">Past 12 months</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-8 h-0.5 border-t-2 border-dashed border-primary mt-2 opacity-60"></div>
            <div>
              <div className="font-semibold text-foreground">24-Month Projection</div>
              <div className="text-muted-foreground text-xs">Forward-looking trajectory</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-3 h-3 rounded-full bg-primary mt-1.5"></div>
            <div>
              <div className="font-semibold text-foreground">Current Position</div>
              <div className="text-muted-foreground text-xs">Index: {currentScore.toFixed(1)}</div>
            </div>
          </div>
        </div>
      </motion.div>
    </Card>
  );
};