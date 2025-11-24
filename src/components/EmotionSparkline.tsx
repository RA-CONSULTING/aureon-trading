import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { Line, LineChart, XAxis, YAxis } from 'recharts';

export default function EmotionSparkline({ 
  data, 
  height=40 
}:{
  data:{t:number;v:number;f:number;a:number}[];
  height?:number
}) {
  const chartData = data.map(d=>({
    time:d.t, 
    value:Math.round(d.v*100)/100
  }));
  
  return (
    <div style={{height}} className="w-full">
      <ChartContainer className="h-full w-full" config={{ value:{label:'Valence'} }}>
        <LineChart data={chartData}>
          <XAxis dataKey="time" hide />
          <YAxis domain={[0,1]} hide />
          <ChartTooltip cursor={false} content={<ChartTooltipContent/>}/>
          <Line 
            type="monotone" 
            dataKey="value" 
            dot={false} 
            strokeWidth={2} 
            isAnimationActive={false}
          />
        </LineChart>
      </ChartContainer>
    </div>
  );
}