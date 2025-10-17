import fs from 'fs';
import path from 'path';

const AI_STATE_DIR = 'D:/AI_Trading_Storage/ai_state';

export function readJSON(fileName) {
  try {
    const fullPath = path.join(AI_STATE_DIR, fileName);
    const data = fs.readFileSync(fullPath, 'utf8');
    return JSON.parse(data);
  } catch (err) {
    console.error('Error reading file:', fileName, err);
    return null;
  }
}

export function getLatestDecision() {
  return readJSON('decision_kernel_state.json');
}

export function getPaperTradingState() {
  return readJSON('paper_trading_state.json');
}
