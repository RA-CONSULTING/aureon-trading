import { useEffect, useRef, useState } from "react";
import { nowMicros, isoTimestamp } from "@/utils/time";

/** High-resolution clock: updates with rAF, exposes microseconds */
export function useHiResClock() {
  const start = useRef(nowMicros());
  const [nowUs, setNowUs] = useState<number>(nowMicros());

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      setNowUs(nowMicros());
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const elapsedUs = nowUs - start.current;
  const iso = isoTimestamp();
  return { nowUs, elapsedUs, iso };
}