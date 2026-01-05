from unittest import TestCase

from src.model import Dollars, FinancialActivityStatement, FinancialActivity, FinancialActivityFileSource
from src.model import FinancialActivityFileLineParser, SingleAmountColumnFileRecordSpec, TwoAmountColumnsFileRecordSpec
from src.model_activityEnrichment import ActivityEnrichmentSpecBuilder
from src.model import FinancialActivityStatementExporter, DescriptionColumnDefinition, AmountColumnDefinition
from src.model import ActivityTypeColumnDefinition, CurrencyColumnDefinition, CategoryColumnDefinition, SourceNameColumnDefinition
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
        aSource = self.sourceWithExpensesFromAmounts([tenDollars, twoDollars, fiveDollars])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        statementExpenses = statement.expenses()
        self.assertListEqual(statementExpenses, aSource.expenses())
    
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
        aSource = self.sourceWithIncomesFromAmounts([tenDollars, twoDollars, fiveDollars, sevenDollars])
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        statementIncomes = statement.incomes()
        self.assertListEqual(statementIncomes, aSource.incomes())

    def zeroDollars(self):
        return Dollars.zero()
    
    def dollars(self,amount):
        return Dollars.withAmount(amount)
    
    def sourceWithSingleExpense(self, anAmount):
        return self.sourceWithExpensesFromAmounts([anAmount])
    
    def sourceWithSingleIncome(self, anAmount):
        return self.sourceWithIncomesFromAmounts([anAmount])

    def sourceWithExpensesFromAmounts(self, amounts):
        return LoadedActivitySource.withExpensesFromAmounts(amounts)

    def sourceWithIncomesFromAmounts(self, amounts):
        return LoadedActivitySource.withIncomesFromAmounts(amounts)


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
        self.assertActivitiesQuantity(expenses, 1)
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
        self.assertActivitiesQuantity(incomes, 1)
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
        self.assertActivitiesQuantity(expenses, 1)
        self.assertActivityDescription(expenses[0], 'PayAPP MarketABC NY #R#')
    
    def testSingleExpenseCategoryIsSourcedAsUnclassifiedIfNoActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP MarketABC NY #R#,Name LastName,-12345,3.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivitiesQuantity(expenses, 1)
        self.assertActivityDescriptionAndCategory(expenses[0], 'PayAPP MarketABC NY #R#', 'Unclassified')
    
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
        self.assertActivityDescription(expenses[0], 'MarketABC')
    
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
        self.assertActivityDescriptionAndCategory(expenses[0], 'MarketABC', 'Groceries')

    def testTwoExpensesAreSourcedWithSameDescriptionAsFileIfNoActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',
                 '14/05/2024,Elect**Co** NY,Name LastName,-12345,50.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityDescription(expenses[0], 'PayAPP Markt#ABC NY #R#')
        self.assertActivityDescription(expenses[1], 'Elect**Co** NY')

    def testTwoExpensesCategoriesAreSourcedAsUnclassifiedIfNoActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',
                 '14/05/2024,Elect**Co** NY,Name LastName,-12345,50.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        activityEnrichmentSpec = self.emptyActivityEnrichmentSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityDescriptionAndCategory(expenses[0], 'PayAPP Markt#ABC NY #R#', 'Unclassified')
        self.assertActivityDescriptionAndCategory(expenses[1], 'Elect**Co** NY', 'Unclassified')
    
    def testTwoExpensesCategoriesAreSourcedAsGroceriesIfActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',
                 '14/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,50.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC','Markt#ABC')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityDescriptionAndCategory(expenses[0], 'MarketABC', 'Groceries')
        self.assertActivityDescriptionAndCategory(expenses[1], 'MarketABC', 'Groceries')
    
    def testTwoExpensesCategoriesAreSourcedAsGroceriesAndElectricityIfActivityRefinementSpecIsGiven(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',
                 '14/05/2024,Elect**Co** NY,Name LastName,-12345,50.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC','Markt#ABC')
        specBuilder.addDefintionSpecForDescriptionIncludingString('Electricity', 'ElectricCompany','Elect**Co** NY')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityDescriptionAndCategory(expenses[0], 'MarketABC', 'Groceries')
        self.assertActivityDescriptionAndCategory(expenses[1], 'ElectricCompany', 'Electricity')

    def testThreeExpensesWithDifferentRawDescriptionsAreClassifiedIntoGroceries(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',
                 '14/05/2024,PayAPP XYZ#Fresh NY #R#,Name LastName,-12345,50.00',
                 '21/05/2024,PayAPP Goods#4#You NY #R#,Name LastName,-12345,27.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'MarketABC','Markt#ABC')
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'XYZ_Fresh','XYZ#Fresh')
        specBuilder.addDefintionSpecForDescriptionIncludingString('Groceries', 'Goods_4_You','Goods#4#You')
        activityEnrichmentSpec = specBuilder.fullSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityDescriptionAndCategory(expenses[0], 'MarketABC', 'Groceries')
        self.assertActivityDescriptionAndCategory(expenses[1], 'XYZ_Fresh', 'Groceries')
        self.assertActivityDescriptionAndCategory(expenses[2], 'Goods_4_You', 'Groceries')
    
    def testThreeExpensesWithDifferentRawDescriptionsAreSourcedWithSameDescrittionAndClassification(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP MarKT#ABC#UpperWest NY #R#,Name LastName,-12345,3.00',
                 '14/05/2024,PayAPP MarKetT#AbC#UpperEast NY #R#,Name LastName,-12345,50.00',
                 '21/05/2024,PayAPP MKT#ABc#Tribeca NY #R#,Name LastName,-12345,27.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        marketABCRawDescriptions = ['MarKT#ABC#UpperWest', 'MarKetT#AbC#UpperEast', 'MKT#ABc#Tribeca']
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForDescriptionIncludingAnyOfGivenStrings('Groceries', 'MarketABC', marketABCRawDescriptions)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityDescriptionCategoryAndTotalInDollars(expenses[0], 'MarketABC', 'Groceries', 3)
        self.assertActivityDescriptionCategoryAndTotalInDollars(expenses[1], 'MarketABC', 'Groceries', 50)
        self.assertActivityDescriptionCategoryAndTotalInDollars(expenses[2], 'MarketABC', 'Groceries', 27)

    def testSingleExpenseDescriptionIsSourcedAsMarketABCIfActivityRefinementSpecIsGivenUsingPlugableCondition(self):
        lines = ['Date,Description,Card Member,Account #,Amount',
                 '12/05/2024,PayAPP Markt#ABC NY #R#,Name LastName,-12345,3.00',]
        aFile = self.fileWithGivenLines(lines)
        spec = SingleAmountColumnFileRecordSpec.forSpecificColumn(descriptionColumn = 'Description', amountColumn = 'Amount')
        parser = FinancialActivityFileLineParser.commaSeparatedValues()
        marketABCCondition = lambda anActivity: 'Markt#ABC' in anActivity.description()
        specBuilder = ActivityEnrichmentSpecBuilder()
        specBuilder.addDefintionSpecForCodeBasedCondition('Groceries', 'MarketABC', marketABCCondition)
        activityEnrichmentSpec = specBuilder.fullSpec()
        aSource = FinancialActivityFileSource.fromFile(aFile, spec, parser, activityEnrichmentSpec)
        expenses = aSource.expenses()
        self.assertActivityDescription(expenses[0], 'MarketABC')

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
    
    def assertActivityDescription(self, anActivity, expectedDescription):
        self.assertEqual(anActivity.description(), expectedDescription)

    def assertActivityCategory(self, anActivity, expectedCategory):
        self.assertEqual(anActivity.category(), expectedCategory)

    def assertActivityTotal(self, anActivity, expectedDollarAmount):
        expectedActivityTotal = Dollars.withAmount(expectedDollarAmount)
        self.assertEqual(anActivity.total(), expectedActivityTotal)

    def assertActivityDescriptionAndCategory(self, anActivity, expectedDescription, expectedCategory):
        self.assertActivityDescription(anActivity, expectedDescription)
        self.assertActivityCategory(anActivity, expectedCategory)

    def assertActivityDescriptionCategoryAndTotalInDollars(self, anActivity, expectedDescription, expectedCategory, expectedDollarAmount):
        self.assertActivityDescription(anActivity, expectedDescription)
        self.assertActivityCategory(anActivity, expectedCategory)
        self.assertActivityTotal(anActivity, expectedDollarAmount)

    def assertActivityWithDescriptionAndCategory(self, activities, aDescription, aCategory):
        matchingActivityWasFound = False
        for anActivity in activities:
            currentActivityMatchesDescription = anActivity.description() == aDescription
            currentActivityMatchesTotal = anActivity.category() == aCategory
            currentActivityMatches = currentActivityMatchesDescription and currentActivityMatchesTotal
            matchingActivityWasFound = matchingActivityWasFound or currentActivityMatches
        self.assertTrue(matchingActivityWasFound, 'No matching activity with expected description and category')

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


class ActivityEnrichmentSpecBuilderTest(TestCase):  

    def testBucketNameCannotBeEmpty(self):
        specBuilder = ActivityEnrichmentSpecBuilder()
        with self.assertRaisesRegex(Exception, 'Bucket name cannot be empty'):
            specBuilder.addDefintionSpecForDescriptionIncludingString('', 'DescriptionOverride','StringInDescription')

    def testStringInActivityDescriptionInclusionConditionCannotBeEmpty(self):
        specBuilder = ActivityEnrichmentSpecBuilder()
        with self.assertRaisesRegex(Exception, 'String to search for cannot be empty'):
            specBuilder.addDefintionSpecForDescriptionIncludingString('Bucket', 'DescriptionOverride','')


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

    def testExportIncludesColumnCategoryShowingGroceriesForAnExpenseActivity(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithDescriptionCategoryAndDollarsAmount('MarketABC', 'Groceries', 6.78)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition(), AmountColumnDefinition(), CategoryColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Description,Amount,Category",
            'MarketABC,-6.78,Groceries'])
    
    def testExportIncludesColumnSourceShowingCashAccountForAnIncomeActivity(self):
        aSource = LoadedActivitySource.withName('CashAccount')
        aSource.addIncomeWithDescriptionAndDollarsAmount('Salary-Work', 2000)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        columnDefinitions = [DescriptionColumnDefinition(), SourceNameColumnDefinition()]
        exporter = FinancialActivityStatementExporter.withColumnDefinitions(columnDefinitions)
        exportedFile = TestFile()
        exporter.exportStatementIntoFile(statement, exportedFile)
        self.assertExportedLines(exportedFile, [
            "Description,Source",
            'Salary-Work,CashAccount'])
    
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
    

