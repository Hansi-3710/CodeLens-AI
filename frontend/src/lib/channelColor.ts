/**
 * Assigns each model a stable "channel" color (see tailwind.config.js's
 * channel.1-6 palette) by hashing its name, so a model's color is
 * consistent across every visualization in the app without needing a
 * central registry to keep in sync.
 *
 * Belongs to: frontend/src/lib/
 * Phase: 7 (Frontend)
 */
const CHANNEL_HEX = ["#E8734A", "#4F7CFF", "#33A373", "#B072D9", "#D9B23C", "#4AAFC7"];

export function channelColorFor(modelName: string): string {
  let hash = 0;
  for (let i = 0; i < modelName.length; i++) {
    hash = (hash * 31 + modelName.charCodeAt(i)) >>> 0;
  }
  return CHANNEL_HEX[hash % CHANNEL_HEX.length];
}
