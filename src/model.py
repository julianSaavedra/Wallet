
class Dollars():
    @classmethod
    def zero(cls):
        return cls.amount(0)
    
    @classmethod
    def amount(cls,amount):
        return cls(amount)
    
    def __init__(self,amount):
        self._amount = amount
    
    def __eq__(self, value):
        return isinstance(value, type(self)) and self._amount == value._amount
    
    def __hash__(self):
        return hash((self._amount, type(self)))
    
    def __str__(self):
        return str(self._amount) + ' ' + 'USD'
    
    def __add__(self, value):
        return Dollars.amount(self._amount + value._amount)

class ExpensesSummary():
    @classmethod
    def fromSources(cls, sources=[]):
        return cls(sources)
    
    def __init__(self, sources):
        self._sources = sources 
    
    def totalExpenses(self):
        return self.sum(self._sources, lambda aSource: self.totalExpensesFromSource(aSource))
  
    def totalExpensesFromSource(self, aSource):
        return self.sum(aSource.expenses(), lambda anExpense: anExpense.total())

    def sum(self, collection, summandsExtractor):
        accumulator = Dollars.zero()
        for anElement in collection:
            accumulator = accumulator + summandsExtractor(anElement)
        return accumulator

class ExpensesFromFileSource():
    @classmethod
    def fromFile(cls, aFile):
        return cls(aFile)
    
    def __init__(self, aFile):
        self._file = aFile

    def expenses(self):
        expenses = []
        lines = self._file.readlines()
        if lines:
            header = lines[0].split(',')
            indexOfAmount = header.index('Debit')
            for line in lines[1:]:
                expenseAmount = line.split(',')[indexOfAmount]
                expense = Expense.withTotal(Dollars.amount(float(expenseAmount)))
                expenses.append(expense)
        return expenses

class Expense():
    @classmethod
    def withTotal(cls,total):
        return cls(total)
    
    def __init__(self, total):
        self._total = total
    
    def total(self):
        return self._total
