from datetime import datetime, timezone
from backend.app.services.peak_alignment import compute_peak_alignment_score

noon_time = datetime(2026, 9, 12, 8, 0, 0, tzinfo=timezone.utc)
print('Score at 08:00 UTC (~1:30pm IST):', compute_peak_alignment_score(noon_time))

midnight_time = datetime(2026, 9, 12, 18, 0, 0, tzinfo=timezone.utc)
print('Score at 18:00 UTC (~11:30pm IST):', compute_peak_alignment_score(midnight_time))
