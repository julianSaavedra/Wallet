
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
        amountString = '{0:.2f}'.format(self._amount)
        return amountString + ' ' + 'USD'
    
    def __add__(self, value):
        return Dollars.amount(self._amount + value._amount)
    
    def __sub__(self, value):
        return Dollars.amount(self._amount - value._amount)


class ExpensesAndIncomeSummary():
    @classmethod
    def fromSources(cls, sources=[]):
        return cls(sources)
    
    def __init__(self, sources):
        self._sources = sources 
    
    def totalExpenses(self):
        return self.sumFromSources(lambda aSource: self.totalExpensesFromSource(aSource))
  
    def totalIncome(self):
        return self.sumFromSources(lambda aSource: self.totalIncomeFromSource(aSource))
    
    def sumFromSources(self, summandsExtractor):
        return self.sum(self._sources, summandsExtractor)

    def totalExpensesFromSource(self, aSource):
        return self.sum(aSource.expenses(), lambda anExpense: anExpense.total())
    
    def totalIncomeFromSource(self, aSource):
        return self.sum(aSource.incomes(), lambda anIncome: anIncome.total())

    def sum(self, collection, summandsExtractor):
        accumulator = Dollars.zero()
        for anElement in collection:
            accumulator = accumulator + summandsExtractor(anElement)
        return accumulator

class ExpensesAndIncomesFromFileSource():
    @classmethod
    def fromFile(cls, file, spec, activityLineParser):
        return cls(file, spec, activityLineParser)
    
    def __init__(self, file, spec, activityLineParser):
        self._file = file
        self._spec = spec
        self._activityLineParser = activityLineParser
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
            header = self._activityLineParser.parse(lines[0])
            for line in lines[1:]:
                lineRecord = self._activityLineParser.parse(line)
                expenseAmount = self._spec.expenseAmountFromLine(header, lineRecord)
                if expenseAmount:
                    anExpense = Expense.withTotal(Dollars.amount(expenseAmount))
                    expenses.append(anExpense)
                incomeAmount = self._spec.incomeAmountFromLine(header, lineRecord)
                if incomeAmount:
                    anIncome = Income.withTotal(Dollars.amount(incomeAmount))
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

class SingleAmountColumnStatementActivityFileSpecification:
    
    @classmethod
    def forSpecificColumn(cls, amountColumn):
        return cls(amountColumn)
    
    def __init__(self, amountColumn):
        self._amountColumn = amountColumn
    
    def expenseAmountFromLine(self, header, lineRecord):
        amount = self._amountAtColumn(header, lineRecord, self._amountColumn)
        return amount if amount is not None and amount > 0 else None

    def incomeAmountFromLine(self, header, lineRecord):
        amount = self._amountAtColumn(header, lineRecord, self._amountColumn)
        return abs(amount) if amount is not None and amount < 0 else None
    
    def _amountAtColumn(self, header, lineRecord, columnName):
        amountIndex = header.index(columnName)
        return float(lineRecord[amountIndex])

class TwoAmountColumnStatementActivityFileSpecification:

    @classmethod
    def forColumns(cls, expenseColumn, incomeColumn):
        return cls(expenseColumn, incomeColumn)

    def __init__(self, expenseColumn, incomeColumn):
        self._expenseColumn = expenseColumn
        self._incomeColumn = incomeColumn
    
    def expenseAmountFromLine(self, header, lineRecord):
        expenseIndex = header.index(self._expenseColumn)
        expenseAmount = lineRecord[expenseIndex]
        return float(expenseAmount) if expenseAmount else None

    def incomeAmountFromLine(self, header, lineRecord):
        incomeIndex = header.index(self._incomeColumn)
        incomeAmount = lineRecord[incomeIndex]
        return float(incomeAmount) if incomeAmount else None


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