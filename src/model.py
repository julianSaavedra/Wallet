from datetime import date


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
    def fromFile(cls, name, file, amountColumnSpec, activityLineParser, activityEnrichmentSpec):
        cls.assertName(name)
        return cls(name, file, amountColumnSpec, activityLineParser, activityEnrichmentSpec)
    
    @classmethod
    def assertName(cls, name):
        if not name: raise Exception('Source name cannot be empty')

    def __init__(self, name, file, amountColumnSpec, activityLineParser,activityEnrichmentSpec):
        self._name = name
        self._file = file
        self._amountColumnSpec = amountColumnSpec
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
    
    def name(self):
        return self._name

    def _loadActivityFromFile(self):
        expenses = []
        incomes = []
        lines = self._file.readlines()
        if lines:
            header = self._activityLineParser.parse(lines[0])
            for line in lines[1:]:
                lineRecord = self._activityLineParser.parse(line)
                activity = self._activityFromRecord(header, lineRecord)
                if activity.isExpense():
                    expenses.append(activity)
                else:
                    incomes.append(activity)
        self._loadedExpenses = expenses
        self._loadedIncomes = incomes
    
    def _activityFromRecord(self, header, lineRecord):
        rawDescription = self._amountColumnSpec.descriptionFromLine(header, lineRecord)
        rawRecord = FileRawActivityRecord.withDescription(rawDescription)
        activityDate = self._amountColumnSpec.dateFromLine(header, lineRecord)
        enrichmentDefinition = self._activityEnrichmentSpec.enrichmentDefinitionForActivity(rawRecord)
        expenseAmount = self._amountColumnSpec.expenseAmountFromLine(header, lineRecord)
        if expenseAmount:
            activity = self._newExpense(rawDescription, enrichmentDefinition, expenseAmount, activityDate)
        incomeAmount = self._amountColumnSpec.incomeAmountFromLine(header, lineRecord)
        if incomeAmount:
            activity = self._newIncome(rawDescription, enrichmentDefinition, incomeAmount, activityDate)
        return activity

    def _newIncome(self, rawDescription, enrichmentDefinition, incomeAmount, activityDate):
        return FinancialActivity.incomeWithDescriptionAndTotal(enrichmentDefinition.descriptionOverride(), rawDescription, enrichmentDefinition.bucket(), Dollars.withAmount(incomeAmount), self, activityDate)

    def _newExpense(self, rawDescription, enrichmentDefinition, expenseAmount, activityDate):
        return FinancialActivity.expenseWithDescriptionAndTotal(enrichmentDefinition.descriptionOverride(), rawDescription, enrichmentDefinition.bucket(), Dollars.withAmount(expenseAmount), self, activityDate)


class FileRawActivityRecord():
    
    @classmethod
    def withDescription(cls, description):
        return cls(description)
    
    def __init__(self, description):
        self._description = description
    
    def description(self):
        return self._description
    


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
    def expenseWithDescriptionAndTotal(cls, aDescription, aRawDescription, aCategory, total, source, aDate):
        return cls.withDescriptionAndTotal(aDescription, aRawDescription, aCategory,'Expense', total, source, aDate)
   
    @classmethod
    def incomeWithDescriptionAndTotal(cls, aDescription, aRawDescription, aCategory, total, source, aDate):
        return cls.withDescriptionAndTotal(aDescription, aRawDescription, aCategory, 'Income', total, source, aDate)
    
    @classmethod
    def withDescriptionAndTotal(cls,description, rawDescription, aCategory , type, total, source, aDate):
        return cls(description, rawDescription, aCategory, type, total, source, aDate)

    def __init__(self, description, rawDescription, aCategory, type, total, source, aDate):
        self._description = description
        self._rawDescription = rawDescription 
        self._category = aCategory
        self._total = total
        self._type = type
        self._source = source
        self._date = aDate
    
    def total(self):
        return self._total
    
    def description(self):
        return self._description
    
    def category(self):
        return self._category
    
    def isExpense(self):
        return self._type == 'Expense'

    def sourceName(self):
        return self._source.name()
    
    def rawDescription(self):
        return self._rawDescription
    
    def date(self):
        return self._date

class FileRecordSpec():

    @classmethod
    def withSpecs(cls, descriptionColumn, amountSpec, dateSpec):
        return cls(descriptionColumn, amountSpec, dateSpec)
    
    def __init__(self, descriptionColumn, amountSpec, dateSpec):
        self._descriptionColumn = descriptionColumn
        self._amountSpec = amountSpec
        self._dateSpec = dateSpec
    
    def descriptionFromLine(self, header, lineRecord):
        descriptionIndex = header.index(self._descriptionColumn)
        return lineRecord[descriptionIndex]
    
    def dateFromLine(self, header, lineRecord):
        return self._dateSpec.dateFromLine(header, lineRecord)

    def expenseAmountFromLine(self, header, lineRecord):
        return self._amountSpec.expenseAmountFromLine(header, lineRecord)

    def incomeAmountFromLine(self, header, lineRecord):
        return self._amountSpec.incomeAmountFromLine(header, lineRecord)

class DateFileRecordSpec():

    @classmethod
    def withSeparatorAndSequence(cls, column, separator, sequence):
        return cls( column, separator, sequence)
    
    def __init__(self, column, separator, sequence):
        self._column = column
        self._separator = separator
        self._sequence = sequence
    
    def dateFromLine(self, header, lineRecord):
        rawDate = self._dateStringFromLine(header, lineRecord)
        #NOT YET AVAILABLE - date.strptime(rawDate, '%m-%d-%y')
        dateParts = rawDate.split(self._separator)
        year = dateParts[self._sequence.index('Year')]
        month = dateParts[self._sequence.index('Month')]
        day = dateParts[self._sequence.index('Day')]
        return date(int(year), int(month), int(day))

    def _dateStringFromLine(self, header, lineRecord):
        dateIndex = header.index(self._column)
        return lineRecord[dateIndex]

class SingleAmountColumnFileRecordSpec():
    
    @classmethod
    def forSpecificColumn(cls, amountColumn):
        return cls(amountColumn)
    
    def __init__(self, amountColumn):
        self._amountColumn = amountColumn
    
    def expenseAmountFromLine(self, header, lineRecord):
        amount = self._amountAtColumn(header, lineRecord, self._amountColumn)
        return amount if amount > 0 else 0
    
    def incomeAmountFromLine(self, header, lineRecord):
        amount = self._amountAtColumn(header, lineRecord, self._amountColumn)
        return abs(amount) if amount < 0 else 0
    
    def _amountAtColumn(self, header, lineRecord, columnName):
        amountIndex = header.index(columnName)
        amount = lineRecord[amountIndex]
        return float(amount) if amount else 0


class TwoAmountColumnsFileRecordSpec():

    @classmethod
    def forColumns(cls, expenseColumn, incomeColumn):
        return cls(expenseColumn, incomeColumn)

    def __init__(self, expenseColumn, incomeColumn):
        self._expenseColumn = expenseColumn
        self._incomeColumn = incomeColumn
    
    def expenseAmountFromLine(self, header, lineRecord):
        return self._amountAtColumn(header, lineRecord, self._expenseColumn)

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


class CurrencyColumnDefinition():

    def name(self):
        return 'Currency'
    
    def entryFromActivity(self, anActivity):
        return (anActivity.total().currency())


class ActivityTypeColumnDefinition():

    def name(self):
        return 'Type'
    
    def entryFromActivity(self, anActivity):
        return 'Expense' if anActivity.isExpense() else 'Income'


class CategoryColumnDefinition():

    def name(self):
        return 'Category'
    
    def entryFromActivity(self, anActivity):
        return anActivity.category()


class SourceNameColumnDefinition():

    def name(self):
        return 'Source'
    
    def entryFromActivity(self, anActivity):
        return anActivity.sourceName()


class RawDescriptionColumnDefinition():
    
    def name(self):
        return 'RawDescription'
    
    def entryFromActivity(self, anActivity):
        return anActivity.rawDescription()


class DateColumnDefinition():

    def name(self):
        return 'Date'
    
    def entryFromActivity(self, anActivity):
        return anActivity.date().isoformat()