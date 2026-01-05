from collections import deque

from src.model import FinancialActivity, Dollars

class LoadedActivitySource():

    @classmethod
    def withActivity(cls, anActivity):
        return cls.withActivities([anActivity])
    
    @classmethod
    def withActivities(cls, activities):
        source = cls()
        for anActivity in activities: source.addActivity(anActivity)
        return source

    def __init__(self):
        self._expenses = []
        self._incomes = []

    def addExpenseWithDescription(self, aDescription):
        self.addExpenseWithDescriptionAndDollarsAmount(aDescription,1)
    
    def addExpenseWithDescriptionAndDollarsAmount(self, aDescription, dollarsAmount):
        newExpense = FinancialActivity.expenseWithDescriptionAndTotal(aDescription, "NoBucket", Dollars.withAmount(dollarsAmount))
        self.addExpense(newExpense)

    def addIncomeWithDescriptionAndDollarsAmount(self, aDescription, dollarsAmount):
        newIncome = FinancialActivity.incomeWithDescriptionAndTotal(aDescription, "NoBucket", Dollars.withAmount(dollarsAmount))
        self.addIncome(newIncome)

    def addActivity(self, anActivity):
        if anActivity.isExpense(): self.addExpense(anActivity)
        else: self.addIncome(anActivity)
    
    def addActivities(self, activities):
        for anActivity in activities: self.addActivity(anActivity)

    def addExpense(self, anExpense):
        self._expenses.append(anExpense)

    def addIncome(self, anIncome):
        self._incomes.append(anIncome)

    def expenses(self):
        return self._expenses

    def incomes(self):
        return self._incomes
    
class TestFile():
    def __init__(self):
        self._content = ''
        self._lines = deque()
    
    def write(self, newContent):
         self._content = self._content + newContent

    def addLine(self, aLine):
        self.write(aLine)
        self.write('\n')
    
    def readlines(self):
        return self._content.splitlines()
    
    def readLine(self):
        return self.contentLines().popleft()
        
    """def __iter__(self):
        iterator = []
        while self._lines: iterator.append(self.readLine())
        return iter(iterator)
    
        def contentLines(self):
        if not self._lines:
            self._lines
        self.contentLines()"""