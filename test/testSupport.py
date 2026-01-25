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

    @classmethod
    def withExpensesFromAmounts(cls, amounts):
        source = cls()
        for anAmount in amounts: source.addExpenseWithAmount(anAmount)
        return source
    
    @classmethod
    def withIncomesFromAmounts(cls, amounts):
        source = cls()
        for anAmount in amounts: source.addIncomeWithAmount(anAmount)
        return source
    
    @classmethod
    def withName(cls, name):
        return cls(name)

    def __init__(self, name = 'LoadedSource'):
        self._name = name
        self._expenses = []
        self._incomes = []

    def addExpenseWithDescription(self, aDescription):
        self.addExpenseWithDescriptionAndDollarsAmount(aDescription,1)

    def addExpenseWithAmount(self, anAmount):
        newExpense = FinancialActivity.expenseWithDescriptionAndTotal('Description', 'RawDescription', 'NoCategory', anAmount, self)
        self.addExpense(newExpense)

    def addExpenseWithCategoryAndDollarsAmount(self, category, dollarsAmount):
        total = Dollars.withAmount(dollarsAmount)
        return self.addExpenseWithCategoryAndTotal(category, total)

    def addExpenseWithCategoryAndTotal(self, category, total):
        newExpense = FinancialActivity.expenseWithDescriptionAndTotal('Description', 'RawDescription', category, total, self)
        self.addExpense(newExpense)

    def addExpenseWithDescriptionCategoryAndDollarsAmount(self, aDescription, aCategory, dollarsAmount):
        newExpense = FinancialActivity.expenseWithDescriptionAndTotal(aDescription, aDescription, aCategory, Dollars.withAmount(dollarsAmount), self)
        self.addExpense(newExpense)

    def addExpenseWithDescriptionAndDollarsAmount(self, aDescription, dollarsAmount):
       self.addExpenseWithDescriptionCategoryAndDollarsAmount(aDescription, 'NoCategory', dollarsAmount)

    def addIncomeWithAmount(self, anAmount):
        newIncome = FinancialActivity.incomeWithDescriptionAndTotal('Description', 'RawDescription', 'NoCategory', anAmount, self)
        self.addIncome(newIncome)

    def addIncomeWithDescriptionAndDollarsAmount(self, aDescription, dollarsAmount):
        newIncome = FinancialActivity.incomeWithDescriptionAndTotal(aDescription, aDescription, 'NoCategory', Dollars.withAmount(dollarsAmount), self)
        self.addIncome(newIncome)
    
    def addIncomeWithDescriptionAndRawDescription(self, aDescription, aRawDescription):
        newIncome = FinancialActivity.incomeWithDescriptionAndTotal(aDescription, aRawDescription, 'NoCategory', Dollars.zero(), self)
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

    def name(self):
        return self._name


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