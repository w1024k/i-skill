import React, { useMemo } from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  AbsoluteFill,
  Sequence,
} from "remotion";

const FPS = 30;
const ARRAY = [64, 34, 25, 12, 22, 11, 90];
const BAR_WIDTH = 80;
const BAR_GAP = 20;
const MAX_HEIGHT = 400;
const MAX_VALUE = Math.max(...ARRAY);

function getBubbleSortSteps(arr: number[]) {
  const steps: Array<{
    array: number[];
    comparing: [number, number] | null;
    swapping: [number, number] | null;
    sorted: number[];
    description: string;
  }> = [];

  const array = [...arr];
  const n = array.length;
  const sorted: number[] = [];

  steps.push({
    array: [...array],
    comparing: null,
    swapping: null,
    sorted: [],
    description: "初始数组",
  });

  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      steps.push({
        array: [...array],
        comparing: [j, j + 1],
        swapping: null,
        sorted: [...sorted],
        description: `比较 ${array[j]} 和 ${array[j + 1]}`,
      });

      if (array[j] > array[j + 1]) {
        steps.push({
          array: [...array],
          comparing: [j, j + 1],
          swapping: [j, j + 1],
          sorted: [...sorted],
          description: `交换 ${array[j]} 和 ${array[j + 1]}`,
        });

        [array[j], array[j + 1]] = [array[j + 1], array[j]];

        steps.push({
          array: [...array],
          comparing: null,
          swapping: null,
          sorted: [...sorted],
          description: `交换完成`,
        });
      }
    }
    sorted.unshift(array[n - i - 1]);
  }
  sorted.unshift(array[0]);

  steps.push({
    array: [...array],
    comparing: null,
    swapping: null,
    sorted: [...sorted],
    description: "排序完成!",
  });

  return steps;
}

const SortBar: React.FC<{
  value: number;
  index: number;
  isComparing: boolean;
  isSwapping: boolean;
  isSorted: boolean;
  frame: number;
  startFrame: number;
}> = ({ value, isComparing, isSwapping, isSorted, frame, startFrame }) => {
  const localFrame = frame - startFrame;
  const height = (value / MAX_VALUE) * MAX_HEIGHT;

  let bgColor = "#4A90D9";
  if (isComparing) bgColor = "#F5A623";
  if (isSwapping) bgColor = "#D0021B";
  if (isSorted) bgColor = "#7ED321";

  const appearProgress = interpolate(localFrame, [0, 15], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = isSwapping
    ? interpolate(localFrame % 20, [0, 10, 20], [1, 1.15, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  return (
    <div
      style={{
        width: BAR_WIDTH,
        height: height * appearProgress,
        backgroundColor: bgColor,
        borderRadius: 8,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-end",
        transform: `scale(${scale})`,
        transition: "background-color 0.15s ease",
        position: "relative",
      }}
    >
      <span
        style={{
          color: "white",
          fontSize: 24,
          fontWeight: "bold",
          marginBottom: 8,
        }}
      >
        {value}
      </span>
    </div>
  );
};

const TitleSequence: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 1.5 * fps], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const subtitleOpacity = interpolate(frame, [1 * fps, 2.5 * fps], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a1a2e",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <h1
        style={{
          color: "#ffffff",
          fontSize: 72,
          fontWeight: "bold",
          opacity: titleOpacity,
          margin: 0,
        }}
      >
        冒泡排序
      </h1>
      <p
        style={{
          color: "#a0a0a0",
          fontSize: 32,
          marginTop: 20,
          opacity: subtitleOpacity,
        }}
      >
        Bubble Sort Algorithm
      </p>
    </AbsoluteFill>
  );
};

const SortVisualization: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const steps = useMemo(() => getBubbleSortSteps(ARRAY), []);

  const totalSortFrames = 24 * fps;
  const sortStartFrame = 3 * fps;
  const localFrame = Math.max(frame - sortStartFrame, 0);

  const stepDuration = Math.floor(totalSortFrames / (steps.length - 1));
  const currentStepIndex = Math.min(
    Math.floor(localFrame / stepDuration),
    steps.length - 1
  );
  const currentStep = steps[currentStepIndex];

  const descriptionOpacity = interpolate(localFrame, [0, 15], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const sortedIndices = new Set<number>();
  const passSize = ARRAY.length - 1 - Math.floor(currentStepIndex / (ARRAY.length));
  for (let i = 0; i < ARRAY.length - 1 - passSize && passSize >= 0; i++) {
    if (currentStep.description === "排序完成!") {
      sortedIndices.add(i);
    }
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a1a2e",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: BAR_GAP,
          marginBottom: 60,
          paddingBottom: 20,
          borderBottom: "3px solid #ffffff33",
        }}
      >
        {currentStep.array.map((value, index) => {
          const isComparing =
            currentStep.comparing?.includes(index) ?? false;
          const isSwapping = currentStep.swapping?.includes(index) ?? false;

          return (
            <SortBar
              key={`${index}-${value}`}
              value={value}
              index={index}
              isComparing={isComparing}
              isSwapping={isSwapping}
              isSorted={sortedIndices.has(index)}
              frame={frame}
              startFrame={sortStartFrame}
            />
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          bottom: 80,
          textAlign: "center",
          opacity: descriptionOpacity,
        }}
      >
        <p
          style={{
            color: "#ffffff",
            fontSize: 28,
            margin: 0,
          }}
        >
          {currentStep.description}
        </p>
      </div>

      <div
        style={{
          position: "absolute",
          top: 40,
          left: 40,
          display: "flex",
          gap: 30,
          fontSize: 18,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 20,
              height: 20,
              backgroundColor: "#F5A623",
              borderRadius: 4,
            }}
          />
          <span style={{ color: "#ffffff" }}>比较中</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 20,
              height: 20,
              backgroundColor: "#D0021B",
              borderRadius: 4,
            }}
          />
          <span style={{ color: "#ffffff" }}>交换中</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 20,
              height: 20,
              backgroundColor: "#7ED321",
              borderRadius: 4,
            }}
          />
          <span style={{ color: "#ffffff" }}>已排序</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const FinalSequence: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sortedArray = [...ARRAY].sort((a, b) => a - b);

  const checkmarkOpacity = interpolate(frame, [0, 15], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const barAppear = interpolate(frame, [0, 20], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a1a2e",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: BAR_GAP,
          marginBottom: 60,
          paddingBottom: 20,
          borderBottom: "3px solid #7ED321",
        }}
      >
        {sortedArray.map((value, index) => (
          <div
            key={index}
            style={{
              width: BAR_WIDTH,
              height: ((value / MAX_VALUE) * MAX_HEIGHT) * barAppear,
              backgroundColor: "#7ED321",
              borderRadius: 8,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "flex-end",
              position: "relative",
            }}
          >
            <span
              style={{
                color: "white",
                fontSize: 24,
                fontWeight: "bold",
                marginBottom: 8,
              }}
            >
              {value}
            </span>
          </div>
        ))}
      </div>

      <div
        style={{
          opacity: checkmarkOpacity,
          textAlign: "center",
        }}
      >
        <h2
          style={{
            color: "#7ED321",
            fontSize: 48,
            margin: 0,
          }}
        >
          ✓ 排序完成
        </h2>
        <p
          style={{
            color: "#a0a0a0",
            fontSize: 24,
            marginTop: 10,
          }}
        >
          时间复杂度: O(n²) | 空间复杂度: O(1)
        </p>
      </div>
    </AbsoluteFill>
  );
};

export const MyComposition = () => {
  const { fps } = useVideoConfig();

  return (
    <>
      <Sequence durationInFrames={3 * fps}>
        <TitleSequence />
      </Sequence>

      <Sequence from={3 * fps} durationInFrames={24 * fps}>
        <SortVisualization />
      </Sequence>

      <Sequence from={27 * fps} durationInFrames={3 * fps}>
        <FinalSequence />
      </Sequence>
    </>
  );
};
