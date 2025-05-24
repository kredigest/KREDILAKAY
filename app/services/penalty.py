from decimal import Decimal
from datetime import datetime

class PenaltyCalculator:
    def __init__(self, loan):
        self.loan = loan
        self.daily_rate = Decimal('0.02')  # 2% par jour
    
    @property
    def days_late(self):
        if not self.loan.start_date:
            return 0
        due_date = self.loan.start_date + timedelta(days=self.loan.duration_days)
        return max((datetime.utcnow().date() - due_date).days, 0)
    
    def calculate_total(self):
        return self.loan.total_due * self.daily_rate * self.days_late
