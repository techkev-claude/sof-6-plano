function plannerApp(tripId) {
  return {
    tripId,
    selectedDay: null,
    selectedBlock: null,
    conflicts: [],
    undoStack: [],
    dirtyFlag: false,
    snapMinutes: parseInt(document.querySelector('meta[name=snap-minutes]')?.content || '15'),

    init() {
      this.updateCurrentTimeLine();
      setInterval(() => this.updateCurrentTimeLine(), 60000);
      this.initDragging();
    },

    selectDay(day) {
      this.selectedDay = day;
    },

    selectBlock(blockId) {
      this.selectedBlock = blockId;
    },

    updateCurrentTimeLine() {
      const line = document.getElementById('current-time-line');
      if (!line) return;
      const now = new Date();
      const minutes = now.getHours() * 60 + now.getMinutes();
      line.style.left = (minutes + 120) + 'px';
    },

    initDragging() {
      const blocks = document.querySelectorAll('[data-block-id]');
      blocks.forEach(el => {
        let startX, startLeft, startMinute;

        el.addEventListener('mousedown', (e) => {
          const fixed = el.dataset.fixed === 'true';
          if (fixed) {
            if (!confirm('Dieser Termin ist fixiert. Trotzdem verschieben?')) return;
          }
          startX = e.clientX;
          startLeft = parseInt(el.style.left);
          startMinute = startLeft - 120;
          e.preventDefault();

          const onMove = (e) => {
            const delta = e.clientX - startX;
            const rawMinute = startMinute + delta;
            const snapped = Math.round(rawMinute / this.snapMinutes) * this.snapMinutes;
            const clamped = Math.max(0, Math.min(1320, snapped));
            el.style.left = (clamped + 120) + 'px';
          };

          const onUp = async () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);

            const newLeft = parseInt(el.style.left);
            const newMinute = newLeft - 120;
            const blockId = el.dataset.blockId;
            const oldStart = el.dataset.start;

            const baseDate = oldStart.split('T')[0];
            const hours = Math.floor(newMinute / 60);
            const mins = newMinute % 60;
            const newStart = `${baseDate}T${String(hours).padStart(2,'0')}:${String(mins).padStart(2,'0')}:00`;

            this.undoStack.push({ blockId, oldLeft: startLeft, oldStart });
            if (this.undoStack.length > 20) this.undoStack.shift();

            this.dirtyFlag = true;
            await this.patchBlock(blockId, newStart);
          };

          document.addEventListener('mousemove', onMove);
          document.addEventListener('mouseup', onUp);
        });
      });
    },

    async patchBlock(blockId, startDatetime) {
      try {
        const resp = await fetch(`/api/blocks/${blockId}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCsrfToken(),
          },
          body: JSON.stringify({ start_datetime: startDatetime }),
        });
        const data = await resp.json();
        if (data.conflicts) {
          this.conflicts = data.conflicts.flatMap(c => [c.block_a, c.block_b]);
        } else {
          this.conflicts = [];
        }
      } catch (e) {
        console.error('patch_block_error', e);
      }
    },

    async undoLast() {
      const last = this.undoStack.pop();
      if (!last) return;
      const el = document.querySelector(`[data-block-id="${last.blockId}"]`);
      if (el) el.style.left = last.oldLeft + 'px';
      await this.patchBlock(last.blockId, last.oldStart);
    },

    async saveManual() {
      try {
        const message = prompt('Commit-Nachricht (optional):') || '';
        await fetch(`/api/trips/${this.tripId}/save`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCsrfToken(),
          },
          body: JSON.stringify({ message }),
        });
        this.dirtyFlag = false;
        alert('Gespeichert!');
      } catch (e) {
        console.error('save_error', e);
      }
    },

    getCsrfToken() {
      const m = document.cookie.match(/csrf_token=([^;]+)/);
      const meta = document.querySelector('meta[name=csrf-token]');
      return m ? decodeURIComponent(m[1]) : (meta ? meta.content : '');
    },
  };
}
