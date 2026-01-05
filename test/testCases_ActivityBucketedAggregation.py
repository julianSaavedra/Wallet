from unittest import TestCase

from src.model import FinancialActivityStatement, Dollars, FinancialActivity
from src.model_activityAggregation import ActivityBucketedAggregation, ActivityBucketDefinition
from src.model_activityEnrichment import ActivityAggregationDefinition, ActivityPluggableCondition
from test.testSupport import LoadedActivitySource


class ActivityBucketedAggregationTest(TestCase):

    def testActivityAggregationIsEmptyIfThereAreNoExpensesAndActivityCategoriesSpecIsUsed(self):
        statement = self.emptyStatement()
        aggregationSpec = ActivityBucketedAggregation.fromActivityCategories()
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation, {})

    def testActivityAggregationIsEmptyIfThereAreNoExpensesAndNoAggregationCategoriesAreGiven(self):
        statement = self.emptyStatement()
        aggregationSpec = ActivityBucketedAggregation.withNoDefinitions()
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation, {})

    def testZeroDollarsAreAggregatedIntoSingleCategorySubscriptionsIfThereIsNoActivity(self):
        statement = self.emptyStatement()
        subscriptionsBucketDefinition = ActivityBucketDefinition.withBucketName('Subscriptions')
        aggregationSpec = ActivityBucketedAggregation.withDefinitionDefaultingToActivityCategory(subscriptionsBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Subscriptions'].total(), Dollars.zero())

    def testZeroDollarsAreAggregatedIntoBothGroceriesAndServiciesCategoriesIfThereIsNoActivity(self):
        statement = self.emptyStatement()
        subscriptionsBucketDefinition = ActivityBucketDefinition.withBucketName('Subscriptions')
        serviciesBucketDefinition = ActivityBucketDefinition.withBucketName('Servicies')
        bucketDefinitions = [subscriptionsBucketDefinition, serviciesBucketDefinition]
        aggregationSpec = ActivityBucketedAggregation.withDefinitionsDefaultingToActivityCategory(bucketDefinitions)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Subscriptions'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['Servicies'].total(), Dollars.zero())

    def testSingleExpenseIsAggregatedToNoBucketWhenNoAggregationCategoriesAreGiven(self):
        twoDollars = self.dollars(2)
        statement = self.statementWithSingleActivityWithTotal(twoDollars)
        aggregationSpec = ActivityBucketedAggregation.withNoDefinitions()
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['NoBucket'].total(), twoDollars)

    def testNoBucketIsTheOnlyBucketWhenThereIsActivityAndNoAggregationCategoriesAreGiven(self):
        twoDollars = self.dollars(2)
        statement = self.statementWithSingleActivityWithTotal(twoDollars)
        aggregationSpec = ActivityBucketedAggregation.withNoDefinitions()
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(len(activityAggregation.keys()), 1)
        self.assertIn('NoBucket', activityAggregation.keys())
    
    def testSingleExpenseIsBucketedIntoGroceriesWithTotalOfTwoDollarsIfBucketDefaultsToActivityCategoryAndNoAggregationCategoriesAreGiven(self):
        twoDollars = self.dollars(2)
        statement = self.statementWithSingleActivityWithCategoryAndTotal('Groceries', twoDollars)
        aggregationSpec = ActivityBucketedAggregation.withDefinitionsDefaultingToActivityCategory([])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)

    def testDefaultBucketNoBucketIsNotIncludedWhenSingleExpenseIsClassifiedIntoGroceries(self):
        twoDollars = self.dollars(2)
        statement = self.statementWithSingleActivityWithCategoryAndTotal('Groceries', twoDollars)
        aggregationSpec = ActivityBucketedAggregation.withDefinitionsDefaultingToActivityCategory([])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Groceries'].total(),twoDollars)
        self.assertNotIn('NoBucket', activityAggregation.keys())

    def testTwoExpensesAreAggregatedIntoNoBucketWithTotalOfFiveDollarsWhenNoAggregationCategoriesAreGiven(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithCategoryAndTotal('Groceries', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithCategoryAndTotal('Groceries', threeDollars)
        statement = self.statementWithActivities([anExpense, anotherExpense])
        aggregationSpec = ActivityBucketedAggregation.withNoDefinitions()
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['NoBucket'].total(),fiveDollars)

    def testTwoExpensesClassifiedAsGroceriesAreBucketedIntoGroceriesWithTotalOfFiveDollarsWhenActivityCategoriesSpecIsUsed(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithCategoryAndTotal('Groceries', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithCategoryAndTotal('Groceries', threeDollars)
        statement = self.statementWithActivities([anExpense, anotherExpense])
        aggregationSpec = ActivityBucketedAggregation.fromActivityCategories()
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['Groceries'].total(),fiveDollars)

    def testSingleExpenseIsBucketedIntoNoBucketInsteadOfFixedExpensesWhenCategoryRentIsNotAllocatedToThatBucket(self):
        oneThousandDollars = self.dollars(1000)
        statement = self.statementWithSingleActivityWithCategoryAndTotal('Rent', oneThousandDollars)
        fixedExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('FixedExpenses', [])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(fixedExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['FixedExpenses'].total(), Dollars.zero())
        self.assertEqual(activityAggregation['NoBucket'].total(), oneThousandDollars)
    
    def testSingleExpenseIsBucketedToFixedExpensesWhenCategoryRentIsAllocatedToThatBucket(self):
        oneThousandDollars = self.dollars(1000)
        statement = self.statementWithSingleActivityWithCategoryAndTotal('Rent', oneThousandDollars)        
        fixedExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('FixedExpenses', ['Rent'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(fixedExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['FixedExpenses'].total(), oneThousandDollars)

    def testSingleExpenseIsAggregatedIntoLifestyleAndNotIntoMedicalBucket(self):
        twoDollars = self.dollars(2)
        statement = self.statementWithSingleActivityWithCategoryAndTotal('Coffee', twoDollars)
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee', 'Snack'])
        medicalExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Medical', ['Pharmacy'])
        aggregationSpec = ActivityBucketedAggregation.withDefinitions([lifestyleExpensesBucketDefinition, medicalExpensesBucketDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertBucketTotal(activityAggregation,'Lifestyle', twoDollars)
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Medical')

    def testTwoDollarsCoffeeExpenseAggregatesIntoLifestyleAndAnotherFiveDollarsExpenseAggregatesToNoBucket(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithCategoryAndTotal('Coffee', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithCategoryAndTotal('Services Bill', threeDollars)
        statement = self.statementWithActivities([anExpense, anotherExpense])
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(lifestyleExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Lifestyle'].total(), twoDollars)
        self.assertEqual(activityAggregation['NoBucket'].total(), threeDollars)

    def testTwoExpensesAreAggregatedIntoNoBucketWithTotalOfFiveDollarsWhenSingleLifestyleBucketDefinitionDoesNotMatch(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithCategoryAndTotal('Groceries', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithCategoryAndTotal('Groceries', threeDollars)
        statement = self.statementWithActivities([anExpense, anotherExpense])
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(lifestyleExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)        
        self.assertBucketTotalIsZeroDollars(activityAggregation, 'Lifestyle')
        self.assertBucketTotal(activityAggregation, 'NoBucket', fiveDollars)

    def testATwoDollarsExpenseGoesIntoLifestyleAndAnotherFiveDollarsExpenseGoesIntoMedical(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithCategoryAndTotal('Coffee', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithCategoryAndTotal('Pharmacy', threeDollars)
        statement = self.statementWithActivities([anExpense, anotherExpense])
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        medicalExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Medical', ['Pharmacy'])
        aggregationSpec = ActivityBucketedAggregation.withDefinitions([lifestyleExpensesBucketDefinition, medicalExpensesBucketDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertBucketTotal(activityAggregation,'Lifestyle', twoDollars)
        self.assertBucketTotal(activityAggregation,'Medical', threeDollars)

    def testTwoExpensesAreAggregatedIntoLifestyleWithTotalOfFiveDollarsAndMedicalTotalsZeroDollars(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithCategoryAndTotal('Coffee', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithCategoryAndTotal('Snack', threeDollars)
        statement = self.statementWithActivities([anExpense, anotherExpense])
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee', 'Snack'])
        medicalExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Medical', ['Pharmacy'])
        aggregationSpec = ActivityBucketedAggregation.withDefinitions([lifestyleExpensesBucketDefinition, medicalExpensesBucketDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertBucketTotal(activityAggregation,'Lifestyle', fiveDollars)
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Medical')

    def testTwoExpensesAreAggregatedIntoBoBUcketWhenBothMedicalAndLifestyleBucketsDoNotMatch(self):
        twoDollars = self.dollars(2)
        anExpense = self.expenseWithCategoryAndTotal('Groceries', twoDollars)
        threeDollars = self.dollars(3)
        anotherExpense = self.expenseWithCategoryAndTotal('Sports', threeDollars)
        statement = self.statementWithActivities([anExpense, anotherExpense])
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        medicalExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Medical', ['Pharmacy'])
        aggregationSpec = ActivityBucketedAggregation.withDefinitions([lifestyleExpensesBucketDefinition, medicalExpensesBucketDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Lifestyle')
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Medical')
        self.assertBucketTotal(activityAggregation,'NoBucket', fiveDollars)

    def testThreeExpensesAreAggregatedIntoEntertainmentWithTotalOfOneHundredDollars(self):
        thirtyFiveDollars = self.dollars(35)
        expenseA = self.expenseWithCategoryAndTotal('Jazz', thirtyFiveDollars)
        fifteenDollars = self.dollars(15)
        expenseB = self.expenseWithCategoryAndTotal('Movies', fifteenDollars)
        fiftyDollars = self.dollars(50)
        expenseC = self.expenseWithCategoryAndTotal('Theatre', fiftyDollars)
        statement = self.statementWithActivities([expenseA, expenseB, expenseC])
        entertainmentExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Entertainment', ['Jazz', 'Movies', 'Theatre'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(entertainmentExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        oneHundredDollars = self.dollars(100)
        self.assertBucketTotal(activityAggregation, 'Entertainment',oneHundredDollars)

    def testThreeExpensesGoIntoNoBucketIfSingleBucketDefinitionEntertainmentDoesNotMatch(self):
        thirtyFiveDollars = self.dollars(35)
        expenseA = self.expenseWithCategoryAndTotal('Jazz', thirtyFiveDollars)
        fifteenDollars = self.dollars(15)
        expenseB = self.expenseWithCategoryAndTotal('Movies', fifteenDollars)
        fiftyDollars = self.dollars(50)
        expenseC = self.expenseWithCategoryAndTotal('Theatre', fiftyDollars)
        statement = self.statementWithActivities([expenseA, expenseB, expenseC])
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(lifestyleExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        oneHundredDollars = self.dollars(100)
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Lifestyle')
        self.assertBucketTotal(activityAggregation,'NoBucket', oneHundredDollars)
    
    def testActivityAggregationDefinitionCannotHaveAnEmptyName(self):
        aCondition = ActivityPluggableCondition.usingCode(lambda anActivity: False)
        with self.assertRaisesRegex(Exception, 'Category name cannot be empty'):
            ActivityAggregationDefinition.withNameAndCondition('', aCondition)

    def dollars(self, aTotalAmountInDollars):
        return Dollars.withAmount(aTotalAmountInDollars)

    def expenseWithCategoryAndTotal(self, aCategory, aTotal):
        return FinancialActivity.expenseWithDescriptionAndTotal('Description', aCategory, aTotal)

    def emptyStatement(self):
        return self.statementWithActivities([])

    def statementWithSingleActivityWithTotal(self, aTotal):
        anExpense = self.expenseWithCategoryAndTotal('Category', aTotal)
        aSource = LoadedActivitySource.withActivity(anExpense)
        return FinancialActivityStatement.fromSingleSource(aSource)

    def statementWithSingleActivityWithCategoryAndTotal(self, aCategory, aTotal):
        anExpense = self.expenseWithCategoryAndTotal(aCategory, aTotal)
        aSource = LoadedActivitySource.withActivity(anExpense)
        return FinancialActivityStatement.fromSingleSource(aSource)

    def statementWithActivities(self, activities):
        aSource = LoadedActivitySource.withActivities(activities)
        statement = FinancialActivityStatement.fromSingleSource(aSource)
        return statement

    def assertBucketTotalIsZeroDollars(self, activityAggregation, bucket):
        self.assertBucketTotal(activityAggregation, bucket, Dollars.zero())

    def assertBucketTotal(self, activityAggregation, bucket, expectedTotal):
        self.assertEqual(activityAggregation[bucket].total(), expectedTotal)
    

class ActivityBucketDefinitionTest(TestCase):

    def testBucketNameCannotBeEmpty(self):
        with self.assertRaisesRegex(Exception, 'Bucket name cannot be empty'):
            ActivityBucketDefinition.withBucketName('')