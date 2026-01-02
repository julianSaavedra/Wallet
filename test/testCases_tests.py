from unittest import TestCase

from src.model import Dollars, FinancialActivityStatement, FinancialActivity, FinancialActivityFileSource
from src.model import FinancialActivityFileLineParser, SingleAmountColumnFileRecordSpec, TwoAmountColumnsFileRecordSpec
from src.model_activityEnrichment import ActivityEnrichmentSpecBuilder
from src.model import FinancialActivityStatementExporter, DescriptionColumnDefinition, AmountColumnDefinition, CurrencyColumnDefinition
from src.model import ActivityTypeColumnDefinition
from src.model import CompositeFinancialActivitiesSource
from test.testSupport import LoadedActivitySource, TestFile


class FinancialActivityStatementTest(TestCase):
  
    def testTotalExpenseFromStatementWithSourceWithNoExpensesIsZeroDollars(self):
        aSource = LoadedActivitySource()
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        totalExpenses = statement.totalExpenses()
        self.assertEqual(totalExpenses, self.zeroDollars())
    
    def testTotalExpenseFromStatementWithSourceWithSingleExpenseIsTenDollars(self):
        tenDollars = self.dollars(10)
        aSource = self.sourceWithSingleExpense(tenDollars)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        totalExpenses = statement.totalExpenses()
        self.assertEqual(totalExpenses, tenDollars)
    
    def testExpensesFromStatementIncludesAllThreeExpensesFromSource(self):
        tenDollars = self.dollars(10)
        twoDollars = self.dollars(2)
        fiveDollars = self.dollars(5)
        expenses = self.expensesFromAmounts([tenDollars, twoDollars, fiveDollars])
        aSource = self.sourceWithActivities(expenses)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        statementExpenses = statement.expenses()
        self.assertListEqual(statementExpenses, expenses)
    
    def testTotalIncomeFromStatementWithSourceWithNoIncomesIsZeroDollars(self):
        aSource = LoadedActivitySource()
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        totalIncome = statement.totalIncome()
        self.assertEqual(totalIncome, self.zeroDollars())

    def testTotalIncomeFromStatementWithSourceWithSingleIncomeIsFiftyDollars(self):
        fiftyDollars = self.dollars(50)
        aSource = self.sourceWithSingleIncome(fiftyDollars)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        totalIncome = statement.totalIncome()
        self.assertEqual(totalIncome, fiftyDollars)

    def testTotalIncomeFromStatementWithSourceWithThreeIncomesIsThirtyNineDollars(self):
        threeDollars = self.dollars(3)
        tenDollars = self.dollars(10)
        twentySixDollars = self.dollars(26)
        aSource = self.sourceWithIncomesFromAmounts([threeDollars, tenDollars, twentySixDollars])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        totalIncome = statement.totalIncome()
        self.assertEqual(totalIncome, self.dollars(39))

    def testIncomesFromStatementIncludesAllFourIncomesFromSource(self):
        tenDollars = self.dollars(10)
        twoDollars = self.dollars(2)
        fiveDollars = self.dollars(5)
        sevenDollars = self.dollars(7)
        incomes = self.incomesFromAmounts([tenDollars, twoDollars, fiveDollars, sevenDollars])
        aSource = self.sourceWithActivities(incomes)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        statementIncomes = statement.incomes()
        self.assertListEqual(statementIncomes, incomes)

    def zeroDollars(self):
        return Dollars.zero()
    
    def dollars(self,amount):
        return Dollars.withAmount(amount)
    
    def sourceWithSingleExpense(self, anAmount):
        return self.sourceWithExpensesFromAmounts([anAmount])
    
    def sourceWithSingleIncome(self, anAmount):
        return self.sourceWithIncomesFromAmounts([anAmount])

    def sourceWithExpensesFromAmounts(self, amounts):
        expenses = self.expensesFromAmounts(amounts)
        return self.sourceWithActivities(expenses)

    def expensesFromAmounts(self, amounts):
        return [FinancialActivity.expenseWithTotal(anAmount) for anAmount in amounts]
    
    def incomesFromAmounts(self, amounts):
        return [FinancialActivity.incomeWithTotal(anAmount) for anAmount in amounts]

    def sourceWithIncomesFromAmounts(self, amounts):
        incomes = self.incomesFromAmounts(amounts)
        return self.sourceWithActivities(incomes)

    def sourceWithActivities(self, activites):
        aSource = LoadedActivitySource()
        aSource.addActivities(activites)
        return aSource


class FinancialActivityFileSourceTest(TestCase):
    def testNoExpensesAreImportedFromEmptyFile(self):
        aFile = self.emptyFile()
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsFileRecordSpec.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivitiesQuantity(expenses,0)
    
    def testNoIncomesAreImportedFromEmptyFile(self):
        aFile = self.emptyFile()
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsFileRecordSpec.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        incomes = aSource.incomes()
        self.assertActivitiesQuantity(incomes,0)
    
    def testSingleExpenseOfTwoDollarsIsImportedFromFileWithDebitAndCreditColumns(self):
        lines = ['Date,Description,Debit,Credit',
                 '09-27-2024,PurchaseA,2.00,',]
        aFile = self.fileWithGivenLines(lines)
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsFileRecordSpec.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivitiesQuantity(expenses, 1)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseA', 2)
    
    def testThreeExpensesOfTwoSixAndTenDollarsAreImportedFromFileWithDebitAndCreditColumns(self):
        lines = ['Date,Description,Debit,Credit',
                 '09-27-2024,PurchaseA,2.00,',
                 '09-27-2024,PurchaseB,6.00,',
                 '09-27-2024,PurchaseC,10.00,',]
        aFile = self.fileWithGivenLines(lines)
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsFileRecordSpec.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseA', 2)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseB', 6)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseC', 10)
    
    def testSingleIncomeOfSevenDollarsIsImportedFromFileWithDebitAndCreditColumns(self):
        lines = ['Date,Description,Debit,Credit',
                 '09-30-2024,IncomeA,,7.85',]
        aFile = self.fileWithGivenLines(lines)
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsFileRecordSpec.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeA', 7.85)
    
    def testThreeIncomesOfTenTwelveAndTwentyDollarsAreImportedFromFileWithDebitAndCreditColumns(self):
        lines = ['Date,Description,Debit,Credit',
                 '09-30-2024,IncomeA,,10.00',
                 '09-30-2024,IncomeB,,12.00',
                 '09-30-2024,IncomeC,,20.00',]
        aFile = self.fileWithGivenLines(lines)
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsFileRecordSpec.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeA', 10)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeB', 12)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeC', 20)
    
    def testTwoIncomesOfTwoAndFourDollarsAndTwoExpensesOfThreeAndFiveAreImportedFromFileWithDebitAndCreditColumns(self):
        lines = ['Date,Description,Debit,Credit',
                 '09-30-2024,IncomeA,,2.00',
                 '09-27-2024,PurchaseA,3.00,',
                 '09-30-2024,IncomeB,,4.00',
                 '09-27-2024,PurchaseB,5.00,',]
        aFile = self.fileWithGivenLines(lines)
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        spec = TwoAmountColumnsFileRecordSpec.forColumns(descriptionColumn = 'Description', expenseColumn = 'Debit', incomeColumn = 'Credit')
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseA', 3)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PurchaseB', 5)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeA', 2)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'IncomeB', 4)
    
    def testSingleExpenseOfThreeDollarsIsImportedFromFileWithSingleAmountColumnWithDebitAndCreditColumns(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,Subway,Name LastName,-12345,3.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'Subway', 3)
    
    def testSingleIncomeOfFiveDollarsIsImportedFromFileWithSingleAmountColumn(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/10/2024,Payment,Name LastName,-12345,-5.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'Payment', 5)
    
    def testTwoIncomesOfTwoAndFourDollarsAndTwoExpensesOfThreeAndFiveAreImportedFromFileWithSingleAmountColumn(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,Subway,Name LastName,-12345,3.00',
                 '12/10/2024,Payment,Name LastName,-12345,-2.00',
                 '12/05/2024,Coffee,Name LastName,-12345,5.00',
                 '12/10/2024,Payment,Name LastName,-12345,-4.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        incomes = aSource.incomes()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'Subway', 3)
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'Coffee', 5)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'Payment', 2)
        self.assertActivityWithDescriptionAndTotalInDollars(incomes, 'Payment', 4)
    
    def testSingleExpenseDescriptionIsSourcedWithSameDescriptionAsFileIfNoActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP MarketABC NY #R#,Name LastName,-12345,3.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'PayAPP MarketABC NY #R#', 3)

    def testSingleExpenseCategoryIsSourcedAsUnclassifiedIfNoActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP MarketABC NY #R#,Name LastName,-12345,3.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertEqual(expenses[0].category(), 'Unclassified')
    
    def testSingleExpenseDescriptionIsSourcedAsMarketABCIfActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC','Markt#ABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityWithDescriptionAndTotalInDollars(expenses, 'MarketABC', 3)
    
    def testSingleExpenseCategoryIsSourcedAsGroceriesIfActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC','Markt#ABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertEqual(expenses[0].category(), 'Groceries')
    
    def assertActivitiesQuantity(self, activities, expectedSize):
        self.assertEqual(len(activities), expectedSize)
    
    def assertActivityWithDescriptionAndTotalInDollars(self, activities, aDescription, aDollarAmount):
        matchingActivityWasFound = False
        expectedActivityTotal = Dollars.withAmount(aDollarAmount)
        for anActivity in activities:
            currentActivityMatchesDescription = anActivity.description() == aDescription
            currentActivityMatchesTotal = anActivity.total() == expectedActivityTotal
            currentActivityMatches = currentActivityMatchesDescription and currentActivityMatchesTotal
            matchingActivityWasFound = matchingActivityWasFound or currentActivityMatches
        self.assertTrue(matchingActivityWasFound, 'No matching activity with expected description and total')
    
    def assertAllAndOnlyTotalsInDollars(self, activities, expectedDollarAmounts):
        self.assertEqual(len(activities), len(expectedDollarAmounts))
        for activity , expectedDollarAmount in zip(activities, expectedDollarAmounts):
            self.assertEqual(activity.total(), Dollars.withAmount(expectedDollarAmount))

    def emptyFile(self):
        return self.fileWithGivenLines([])

    def fileWithGivenLines(self, lines):
        aFile = TestFile()
        for aLine in lines: aFile.addLine(aLine)
        return aFile

    def emptyActivityEnrichmentSpec(self):
        specBuilder = ActivityEnrichmentSpecBuilder()
        return specBuilder.fullSpec()


class FinancialActivityFileLineParserTest(TestCase):
    def testLineWithFourCommaSeparatedValuesIsParsedIntoAListWithThoseFourValues(self):
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$,Hello,1.0')
        self.assertEqual(parsedLine, ['A', '$', 'Hello', '1.0'])

    def testLineWithNoValueAfterTheFirstCommaIsParsedIntoAListWithAnEmptyStringsInSecondPlace(self):
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,,Hello,1.0')
        self.assertEqual(parsedLine, ['A', '', 'Hello', '1.0'])

    def testLineWithNoValueAfterLastCommaIsParsedIntoAListWithAnEmptyStringAtTheEnd(self):
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$,Hello,')
        self.assertEqual(parsedLine, ['A', '$', 'Hello', ''])
    
    def testLineWithNoValueBeforeFirstCommaIsParsedIntoAListWithAnEmptyStringAtTheFirstPlace(self):
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse(',$,Hello,1.0')
        self.assertEqual(parsedLine, ['', '$', 'Hello', '1.0'])
    
    def testWhiteSpacesAtTheStartOrEndOfCommaSeparatedValuesAreIgnored(self):
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        parsedLine = parser.parse('A,$ , Hello World,1.0\n')
        self.assertEqual(parsedLine, ['A', '$', 'Hello World', '1.0'])
    
    def testLinesSectionWithCommaWithinQuotesIsParsedAsASingleValue(self):
        parser = FinancialActivityFileLineParser.commaSeparatedValues(boundingCharacter='"')
        parsedLine = parser.parse('123,"NY,USA",456')
        self.assertEqual(parsedLine, ['123', 'NY,USA', '456'])


class FinancialActivityStatementExporterTest(TestCase):

    def testExportUsingNoColumnDefinitionsIsEmptyEvenIfStatementHasActivity(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescription('CoffeeStoreABC')
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        exporter = FinancialActivityStatementExporter.withColumnDefinitions([])
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        exportedFileLines = exportedFile.readlines()
        self.assertEmpty(exportedFileLines)

    def testExportForAnEmptyStatementHasHeaderOnly(self):
        aSource = LoadedActivitySource()
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile,["Description"])
    
    def testExportForStatementWithSingleActivityHasAHeaderAndRowWithTheActivityDescription(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescription('CoffeeStoreABC')
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, ["Description", 'CoffeeStoreABC'])
    
    def testExportForStatementWithThreeActivitiesHasRowForAllThreeActivities(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescription('CoffeeStoreABC')
        aSource.addExpenseWithDescription('MoviesApp123')
        aSource.addExpenseWithDescription('Groceries-R-Us')
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, ["Description", 'CoffeeStoreABC', 'MoviesApp123', 'Groceries-R-Us'])
    
    def testExportIncudesColumnsDescriptionAndAmountForAllThreeActivities(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescriptionAndDollarsAmount('CoffeeStoreABC', 5)
        aSource.addExpenseWithDescriptionAndDollarsAmount('MoviesApp123', 16.99)
        aSource.addExpenseWithDescriptionAndDollarsAmount('Groceries-R-Us', 27.54)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition(), AmountColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Description,Amount",
            'CoffeeStoreABC,-5.00',
            'MoviesApp123,-16.99',
            'Groceries-R-Us,-27.54'])
    
    def testExportIncudesColumnsDescriptionCurrencyAndAmountForAllThreeActivities(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescriptionAndDollarsAmount('CoffeeStoreABC', 5)
        aSource.addExpenseWithDescriptionAndDollarsAmount('MoviesApp123', 16.99)
        aSource.addExpenseWithDescriptionAndDollarsAmount('Groceries-R-Us', 27.54)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition(), CurrencyColumnDefinition(), AmountColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Description,Currency,Amount",
            'CoffeeStoreABC,USD,-5.00',
            'MoviesApp123,USD,-16.99',
            'Groceries-R-Us,USD,-27.54'])

    def testExportColumnsAreSortedAsCurrencyAmountAndDescription(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescriptionAndDollarsAmount('CoffeeStoreABC', 5)
        aSource.addExpenseWithDescriptionAndDollarsAmount('MoviesApp123', 16.99)
        aSource.addExpenseWithDescriptionAndDollarsAmount('Groceries-R-Us', 27.54)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [CurrencyColumnDefinition(), AmountColumnDefinition(),DescriptionColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Currency,Amount,Description",
            'USD,-5.00,CoffeeStoreABC',
            'USD,-16.99,MoviesApp123',
            'USD,-27.54,Groceries-R-Us'])

    def testExportExpenseAmountsAsNegativeAndIncomeAmountAsPositive(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescriptionAndDollarsAmount('CoffeeStoreABC', 5)
        aSource.addExpenseWithDescriptionAndDollarsAmount('MoviesApp123', 16.99)
        aSource.addIncomeWithDescriptionAndDollarsAmount('Salary-Work', 2000)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [CurrencyColumnDefinition(), AmountColumnDefinition(),DescriptionColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Currency,Amount,Description",
            'USD,-5.00,CoffeeStoreABC',
            'USD,-16.99,MoviesApp123',
            'USD,2000.00,Salary-Work'])
    
    def testExportIncludesTheActivityFromThreeDifferentSources(self):
        sourceA = LoadedActivitySource()
        sourceA.addExpenseWithDescriptionAndDollarsAmount('CoffeeStoreABC', 5)
        sourceB = LoadedActivitySource()
        sourceB.addExpenseWithDescriptionAndDollarsAmount('MoviesApp123', 16.99)
        sourceC = LoadedActivitySource()
        sourceC.addIncomeWithDescriptionAndDollarsAmount('Salary-Work', 2000)
        aSource = CompositeFinancialActivitiesSource.withAllSources([sourceA, sourceB, sourceC])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [CurrencyColumnDefinition(), AmountColumnDefinition(),DescriptionColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Currency,Amount,Description",
            'USD,-5.00,CoffeeStoreABC',
            'USD,-16.99,MoviesApp123',
            'USD,2000.00,Salary-Work'])
    
    def testExportIncludesColumnTypeShowingExpenseForAnExpenseActivity(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescriptionAndDollarsAmount('CoffeeStoreABC', 5)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition(), ActivityTypeColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Description,Type",
            'CoffeeStoreABC,Expense'])
    
    def testExportIncludesColumnTypeShowingIncomesForAnIncomeActivity(self):
        aSource = LoadedActivitySource()
        aSource.addIncomeWithDescriptionAndDollarsAmount('Salary-Work', 2000)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition(), ActivityTypeColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Description,Type",
            'Salary-Work,Income'])

    def assertEmpty(self, aCollection):
        self.assertEqual(len(aCollection),0)
    
    def assertExportedLines(self, exportedFile, expectedLines):
        exportedFileLines = exportedFile.readlines()
        self.assertEqual(exportedFileLines, expectedLines)


class DollarsTests(TestCase):
    def testEquals(self):
        aZeroDollars = Dollars.zero()
        anotherZeroDollars = Dollars.zero()
        twoDollars = Dollars.withAmount(2)
        self.assertEqual(aZeroDollars, anotherZeroDollars)
        self.assertNotEqual(aZeroDollars, twoDollars)        
    
    def testHash(self):
        aZeroDollars = Dollars.zero()
        anotherZeroDollars = Dollars.zero()
        twoDollars = Dollars.withAmount(2)
        self.assertEqual(hash(aZeroDollars), hash(anotherZeroDollars))
        self.assertNotEqual(hash(aZeroDollars), hash(twoDollars))
    
    def testCurrency(self):
        twoDollars = Dollars.withAmount(2)
        self.assertEqual(twoDollars.currency(), 'USD')

    def testAmount(self):
        twoDollars = Dollars.withAmount(2)
        self.assertEqual(twoDollars.amount(), 2)

    def testStringRepresentation(self):
        zeroDollars = Dollars.zero()
        self.assertEqual(str(zeroDollars), '0.00 USD')
        twoDollars = Dollars.withAmount(2)
        self.assertEqual(str(twoDollars), '2.00 USD')
        oneDollarAndAThird = Dollars.withAmount(1 + 1/3)
        self.assertEqual(str(oneDollarAndAThird), '1.33 USD')
    
    def testTwoDollarsPlusFiveDollarsEqualsSevenDollars(self):
        twoDollars = Dollars.withAmount(2)
        fiveDollars = Dollars.withAmount(5)
        sevenDollars = Dollars.withAmount(7)
        self.assertEqual(twoDollars + fiveDollars, sevenDollars)
    
    def testTwentyDollarsMinusFourteenDollarsEqualsSixDollars(self):
        twentyDollars = Dollars.withAmount(20)
        fourteenDollars = Dollars.withAmount(14)
        sixDollars = Dollars.withAmount(6)
        self.assertEqual(twentyDollars - fourteenDollars, sixDollars)
    

