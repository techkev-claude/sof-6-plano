window.dirtyFlag = false;

setInterval(async () => {
  if (!window.dirtyFlag || !window.currentTripId) return;
  try {
    const resp = await fetch(`/api/trips/${window.currentTripId}/autosave`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
    });
    if (resp.ok) {
      window.dirtyFlag = false;
      console.log('[autosave] saved');
    }
  } catch (e) {
    console.warn('[autosave] failed', e);
  }
}, 60000);

function getCsrfToken() {
  const m = document.cookie.match(/csrf_token=([^;]+)/);
  const meta = document.querySelector('meta[name=csrf-token]');
  return m ? decodeURIComponent(m[1]) : (meta ? meta.content : '');
}
