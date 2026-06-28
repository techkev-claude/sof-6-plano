const undoStack = [];
const MAX_UNDO = 20;

function pushUndo(state) {
  undoStack.push(state);
  if (undoStack.length > MAX_UNDO) undoStack.shift();
}

function popUndo() {
  return undoStack.pop();
}
