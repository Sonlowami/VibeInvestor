class SessionState:
    def __init__(self, session_id, user_query):
        self.session_id = session_id
        self.user_query = user_query
        self.plan = None
        self.selected_tickers = []
        self.financials= {}
        self.metrics = {}