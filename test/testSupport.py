

class LoadedExpensesAndIncomesSource():
    def __init__(self):
        self._expenses = []
        self._incomes = []

    def addExpense(self, anExpense):
        self._expenses.append(anExpense)

    def addIncome(self, anIncome):
        self._incomes.append(anIncome)

    def expenses(self):
        return self._expenses

    def incomes(self):
        return self._incomes