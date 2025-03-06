from src.model import StatementActivity, Dollars

class LoadedActivitySource():
    def __init__(self):
        self._expenses = []
        self._incomes = []

    def addExpenseWithDescription(self, aDescription):
        newExpense = StatementActivity.expenseWithDescriptionAndTotal(aDescription, Dollars.amount(1))
        self.addExpense(newExpense)
    
    def addExpense(self, anExpense):
        self._expenses.append(anExpense)

    def addIncome(self, anIncome):
        self._incomes.append(anIncome)

    def expenses(self):
        return self._expenses

    def incomes(self):
        return self._incomes