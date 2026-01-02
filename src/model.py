class Dollars():
    @classmethod
    def zero(cls):
        return cls.withAmount(0)

    @classmethod
    def withAmount(cls,amount):
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
        return Dollars.withAmount(self._amount + value._amount)
    
    def __sub__(self, value):
        return Dollars.withAmount(self._amount - value._amount)

    def currency(self):
        return 'USD'

    def amount(self):
        return self._amount


class FinancialActivityStatement():
    @classmethod
    def fromSingleSource(cls, aSource):
        return cls(aSource)

    def __init__(self, aSource):
        self._source = aSource 
    
    def totalExpenses(self):
        return self.sumActivitiesTotal(self.expenses())
  
    def totalIncome(self):
        return self.sumActivitiesTotal(self.incomes())
    
    def activityAggregationBasedOnSpec(self, aggregationSpec):
        return aggregationSpec.aggregatedResultsFromActivities(self.allActivities())
    
    def expenses(self):
        return self._source.expenses()

    def incomes(self):
        return self._source.incomes()

    def allActivities(self):
        return self.expenses() + self.incomes()
    
    def sumActivitiesTotal(self, activities):
        total = Dollars.zero()
        for anActivity in activities:
            total = total + anActivity.total()
        return total


class FinancialActivityFileSource():
    @classmethod
    def fromFile(cls, file, spec, activityLineParser, activityEnrichmentSpec):
        return cls(file, spec, activityLineParser, activityEnrichmentSpec)
    
    def __init__(self, file, spec, activityLineParser,activityEnrichmentSpec):
        self._file = file
        self._spec = spec
        self._activityLineParser = activityLineParser
        self._activityEnrichmentSpec = activityEnrichmentSpec
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
            recordToActivityTransformation = FinancialActivityFileRecordToActivityTransformation()
            for line in lines[1:]:
                lineRecord = self._activityLineParser.parse(line)
                activity = recordToActivityTransformation.activityFromRecord(header, self._spec, self._activityEnrichmentSpec, lineRecord)
                if activity.isExpense():
                    expenses.append(activity)
                else:
                    incomes.append(activity)
        self._loadedExpenses = expenses
        self._loadedIncomes = incomes


class CompositeFinancialActivitiesSource():
    @classmethod
    def withAllSources(cls, sources):
        return cls(sources)
    
    def __init__(self, sources):
        self._sources = sources

    def expenses(self):
        allExpenses = []
        for aSource in self._sources: allExpenses = allExpenses + aSource.expenses()
        return allExpenses
    
    def incomes(self):
        allIncomes = []
        for aSource in self._sources: allIncomes = allIncomes + aSource.incomes()
        return allIncomes


class FinancialActivity():
    @classmethod
    def expenseWithTotal(cls, total):
        return cls.expenseWithDescriptionAndTotal('No Description', 'Unclassified', total)
    
    @classmethod
    def expenseWithDescriptionAndTotal(cls, aDescription, aBucket, total):
        return cls.withDescriptionAndTotal(aDescription, aBucket,'Expense', total)

    @classmethod
    def incomeWithTotal(cls, total):
        return cls.incomeWithDescriptionAndTotal('No Description', 'Unclassified', total)
    
    @classmethod
    def incomeWithDescriptionAndTotal(cls, aDescription, aBucket, total):
        return cls.withDescriptionAndTotal(aDescription, aBucket, 'Income', total)
    
    @classmethod
    def withDescriptionAndTotal(cls,description, aBucket , type, total):
        return cls(description, aBucket, type, total)

    def __init__(self, description, aBucket, type, total):
        self._description = description
        self._bucket = aBucket
        self._total = total
        self._type = type
    
    def total(self):
        return self._total
    
    def description(self):
        return self._description
    
    def category(self):
        return self._bucket
    
    def isExpense(self):
        return self._type == 'Expense'


class FinancialActivityFileRecordToActivityTransformation():

    def activityFromRecord(self, header, spec, activityEnrichmentSpec, lineRecord):
        rawDescription = spec.descriptionFromLine(header, lineRecord)
        enrichmentDefinition = activityEnrichmentSpec.enrichmentDefinitionForRawDescription(rawDescription)
        expenseAmount = spec.expenseAmountFromLine(header, lineRecord)
        if expenseAmount:
            return FinancialActivity.expenseWithDescriptionAndTotal(enrichmentDefinition.descriptionOverride(), enrichmentDefinition.bucket(), Dollars.withAmount(expenseAmount))
        incomeAmount = spec.incomeAmountFromLine(header, lineRecord)
        if incomeAmount:
            return FinancialActivity.incomeWithDescriptionAndTotal(enrichmentDefinition.descriptionOverride(), enrichmentDefinition.bucket(), Dollars.withAmount(incomeAmount))
    

class SingleAmountColumnFileRecordSpec:
    
    @classmethod
    def forSpecificColumn(cls, descriptionColumn, amountColumn):
        return cls(descriptionColumn, amountColumn)
    
    def __init__(self, descriptionColumn, amountColumn):
        self._descriptionColumn = descriptionColumn
        self._amountColumn = amountColumn
    
    def expenseAmountFromLine(self, header, lineRecord):
        amount = self._amountAtColumn(header, lineRecord, self._amountColumn)
        return amount if amount > 0 else 0
    
    def descriptionFromLine(self, header, lineRecord):
        descriptionIndex = header.index(self._descriptionColumn)
        return lineRecord[descriptionIndex]

    def incomeAmountFromLine(self, header, lineRecord):
        amount = self._amountAtColumn(header, lineRecord, self._amountColumn)
        return abs(amount) if amount < 0 else 0
    
    def _amountAtColumn(self, header, lineRecord, columnName):
        amountIndex = header.index(columnName)
        amount = lineRecord[amountIndex]
        return float(amount) if amount else 0


class TwoAmountColumnsFileRecordSpec:

    @classmethod
    def forColumns(cls, descriptionColumn, expenseColumn, incomeColumn):
        return cls(descriptionColumn, expenseColumn, incomeColumn)

    def __init__(self, descriptionColumn, expenseColumn, incomeColumn):
        self._descriptionColumn = descriptionColumn
        self._expenseColumn = expenseColumn
        self._incomeColumn = incomeColumn
    
    def expenseAmountFromLine(self, header, lineRecord):
        return self._amountAtColumn(header, lineRecord, self._expenseColumn)

    def descriptionFromLine(self, header, lineRecord):
        descriptionIndex = header.index(self._descriptionColumn)
        return lineRecord[descriptionIndex]

    def incomeAmountFromLine(self, header, lineRecord):
        return self._amountAtColumn(header, lineRecord, self._incomeColumn)
    
    def _amountAtColumn(self, header, lineRecord, columnName):
        amountIndex = header.index(columnName)
        amount = lineRecord[amountIndex]
        return float(amount) if amount else 0


class FinancialActivityFileLineParser():

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
    

class FinancialActivityStatementExporter():
    
    @classmethod
    def withColumnDefinitions(cls, columnDefinitions):
        return cls(columnDefinitions)

    def __init__(self, columnDefinitions):
        self._columnDefinitions = columnDefinitions

    def exportStatementIntoFile(self, aStatement, aFile):
        if self._columnDefinitions:
            self.addLineToFile(self.headerRow(),aFile)
            for anActivity in aStatement.allActivities():
                newLine = self.lineForActivity(anActivity)
                self.addLineToFile(newLine,aFile)

    def headerRow(self):
        headerNames = [aColumnDefinition.name() for aColumnDefinition in self._columnDefinitions ]
        return self._lineFromEntries(headerNames)
    
    def addLineToFile(self, aLine, aFile):
            aFile.write(aLine + '\n')     

    def lineForActivity(self, anActivity):
        rowEntries = [aColumnDefinition.entryFromActivity(anActivity) for aColumnDefinition in self._columnDefinitions ]
        return self._lineFromEntries(rowEntries)

    def _lineFromEntries(self, entries):
        return ','.join(entries)


class DescriptionColumnDefinition():
    
    def name(self):
        return 'Description'
    
    def entryFromActivity(self, anActivity):
        return anActivity.description()


class AmountColumnDefinition():
    
    def name(self):
        return 'Amount'
    
    def entryFromActivity(self, anActivity):
        activityTotal = anActivity.total()
        sign = '-' if anActivity.isExpense() else '' 
        return sign + '{0:.2f}'.format(activityTotal.amount())


class CurrencyColumnDefinition:

    def name(self):
        return 'Currency'
    
    def entryFromActivity(self, anActivity):
        return (anActivity.total().currency())


class ActivityTypeColumnDefinition:

    def name(self):
        return 'Type'
    
    def entryFromActivity(self, anActivity):
        return 'Expense' if anActivity.isExpense() else 'Income'