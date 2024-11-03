
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
        self._parser = StatementActivityLineParser()
        self._loadedExpenses = []
        self._loadedIncomes = []

    def expenses(self):
        if not self._loadedExpenses: self._loadActivityFromFile()
        return self._loadedExpenses
    
    def incomes(self):
        if not self._loadedIncomes: self._loadActivityFromFile()
        return self._loadedIncomes
        
    def _loadActivityFromFile(self):
        expenses = []
        incomes = []
        lines = self._file.readlines()
        if lines:
            header = self._parser.parse(lines[0])
            indexOfExpense = header.index('Debit')
            indexOfIncome = header.index('Credit')
            for line in lines[1:]:
                expenseAmount = self._parser.parse(line)[indexOfExpense]
                if expenseAmount:
                    anExpense = Expense.withTotal(Dollars.amount(float(expenseAmount)))
                    expenses.append(anExpense)
                incomeAmount = self._parser.parse(line)[indexOfIncome]
                if incomeAmount:
                    anIncome = Income.withTotal(Dollars.amount(float(incomeAmount)))
                    incomes.append(anIncome)
        self._loadedExpenses = expenses
        self._loadedIncomes = incomes


class Expense():
    @classmethod
    def withTotal(cls,total):
        return cls(total)
    
    def __init__(self, total):
        self._total = total
    
    def total(self):
        return self._total

class Income():
    @classmethod
    def withTotal(cls,total):
        return cls(total)
    
    def __init__(self,total):
        self._total = total
    
    def total(self):
        return self._total


class StatementActivityLineParser():

    @classmethod
    def commaSeparatedValues(cls,boundingCharacter = None):
        return cls(',', boundingCharacter)
    
    def __init__(self, separator, boundingCharacter):
        self._separator = separator
        self._boundingCharacter = boundingCharacter

    def parse(self, line):
        parsedValues = []
        currentValue = ''
        ignoreSeparator = False
        for character in line:
            if character == self._separator and not ignoreSeparator:
                parsedValues.append(currentValue)
                currentValue = ''
            elif character == self._boundingCharacter:
                ignoreSeparator = not ignoreSeparator
            else: currentValue = currentValue + character
        parsedValues.append(currentValue)
        return [ parsedValue.strip() for parsedValue in parsedValues ]