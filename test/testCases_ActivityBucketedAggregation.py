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
        aSource = LoadedActivitySource()
        aSource.addExpenseWithCategoryAndDollarsAmount('Groceries', 2)
        aSource.addExpenseWithCategoryAndDollarsAmount('Groceries', 3)
        statement = self.statementWithSource(aSource)
        aggregationSpec = ActivityBucketedAggregation.withNoDefinitions()
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertEqual(activityAggregation['NoBucket'].total(),fiveDollars)

    def testTwoExpensesClassifiedAsGroceriesAreBucketedIntoGroceriesWithTotalOfFiveDollarsWhenActivityCategoriesSpecIsUsed(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithCategoryAndDollarsAmount('Groceries', 2)
        aSource.addExpenseWithCategoryAndDollarsAmount('Groceries', 3)
        statement = self.statementWithSource(aSource)
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
        aSource = LoadedActivitySource()
        twoDollars = self.dollars(2)
        aSource.addExpenseWithCategoryAndTotal('Coffee', twoDollars)
        threeDollars = self.dollars(3)
        aSource.addExpenseWithCategoryAndTotal('Services Bill', threeDollars)
        statement = self.statementWithSource(aSource)
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(lifestyleExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertEqual(activityAggregation['Lifestyle'].total(), twoDollars)
        self.assertEqual(activityAggregation['NoBucket'].total(), threeDollars)

    def testTwoExpensesAreAggregatedIntoNoBucketWithTotalOfFiveDollarsWhenSingleLifestyleBucketDefinitionDoesNotMatch(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithCategoryAndDollarsAmount('Groceries', 2)
        aSource.addExpenseWithCategoryAndDollarsAmount('Groceries', 3)
        statement = self.statementWithSource(aSource)
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(lifestyleExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)        
        self.assertBucketTotalIsZeroDollars(activityAggregation, 'Lifestyle')
        self.assertBucketTotal(activityAggregation, 'NoBucket', fiveDollars)

    def testATwoDollarsExpenseGoesIntoLifestyleAndAnotherFiveDollarsExpenseGoesIntoMedical(self):
        aSource = LoadedActivitySource()
        twoDollars = self.dollars(2)
        aSource.addExpenseWithCategoryAndTotal('Coffee', twoDollars)
        threeDollars = self.dollars(3)
        aSource.addExpenseWithCategoryAndTotal('Pharmacy', threeDollars)
        statement = self.statementWithSource(aSource)
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        medicalExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Medical', ['Pharmacy'])
        aggregationSpec = ActivityBucketedAggregation.withDefinitions([lifestyleExpensesBucketDefinition, medicalExpensesBucketDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        self.assertBucketTotal(activityAggregation,'Lifestyle', twoDollars)
        self.assertBucketTotal(activityAggregation,'Medical', threeDollars)

    def testTwoExpensesAreAggregatedIntoLifestyleWithTotalOfFiveDollarsAndMedicalTotalsZeroDollars(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithCategoryAndDollarsAmount('Coffee', 2)
        aSource.addExpenseWithCategoryAndDollarsAmount('Snack', 3)
        statement = self.statementWithSource(aSource)
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee', 'Snack'])
        medicalExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Medical', ['Pharmacy'])
        aggregationSpec = ActivityBucketedAggregation.withDefinitions([lifestyleExpensesBucketDefinition, medicalExpensesBucketDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertBucketTotal(activityAggregation,'Lifestyle', fiveDollars)
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Medical')

    def testTwoExpensesAreAggregatedIntoBoBUcketWhenBothMedicalAndLifestyleBucketsDoNotMatch(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithCategoryAndDollarsAmount('Groceries', 2)
        aSource.addExpenseWithCategoryAndDollarsAmount('Sports', 3)
        statement = self.statementWithSource(aSource)
        lifestyleExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Lifestyle', ['Coffee'])
        medicalExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Medical', ['Pharmacy'])
        aggregationSpec = ActivityBucketedAggregation.withDefinitions([lifestyleExpensesBucketDefinition, medicalExpensesBucketDefinition])
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        fiveDollars = self.dollars(5)
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Lifestyle')
        self.assertBucketTotalIsZeroDollars(activityAggregation,'Medical')
        self.assertBucketTotal(activityAggregation,'NoBucket', fiveDollars)

    def testThreeExpensesAreAggregatedIntoEntertainmentWithTotalOfOneHundredDollars(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithCategoryAndDollarsAmount('Jazz', 35)
        aSource.addExpenseWithCategoryAndDollarsAmount('Movies', 15)
        aSource.addExpenseWithCategoryAndDollarsAmount('Theatre', 50)
        statement = self.statementWithSource(aSource)
        entertainmentExpensesBucketDefinition = ActivityBucketDefinition.withBucketNameAndActivityCategories('Entertainment', ['Jazz', 'Movies', 'Theatre'])
        aggregationSpec = ActivityBucketedAggregation.withDefinition(entertainmentExpensesBucketDefinition)
        activityAggregation = statement.activityAggregationBasedOnSpec(aggregationSpec)
        oneHundredDollars = self.dollars(100)
        self.assertBucketTotal(activityAggregation, 'Entertainment',oneHundredDollars)

    def testThreeExpensesGoIntoNoBucketIfSingleBucketDefinitionEntertainmentDoesNotMatch(self):
        aSource = LoadedActivitySource()
        aSource.addExpenseWithCategoryAndDollarsAmount('Jazz', 35)
        aSource.addExpenseWithCategoryAndDollarsAmount('Movies', 15)
        aSource.addExpenseWithCategoryAndDollarsAmount('Theatre', 50)
        statement = self.statementWithSource(aSource)
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

    def emptyStatement(self):
        return self.statementWithSource(self.emptySource())

    def statementWithSingleActivityWithTotal(self, aTotal):
        return self.statementWithSingleActivityWithCategoryAndTotal('Category', aTotal)

    def statementWithSingleActivityWithCategoryAndTotal(self, aCategory, aTotal):
        aSource = self.emptySource()
        aSource.addExpenseWithCategoryAndTotal(aCategory, aTotal)
        return FinancialActivityStatement.fromSingleSource(aSource)

    def emptySource(self):
        return LoadedActivitySource()

    def statementWithSource(self, aSource):
        return FinancialActivityStatement.fromSingleSource(aSource)

    def assertBucketTotalIsZeroDollars(self, activityAggregation, bucket):
        self.assertBucketTotal(activityAggregation, bucket, Dollars.zero())

    def assertBucketTotal(self, activityAggregation, bucket, expectedTotal):
        self.assertEqual(activityAggregation[bucket].total(), expectedTotal)
    

class ActivityBucketDefinitionTest(TestCase):

    def testBucketNameCannotBeEmpty(self):
        with self.assertRaisesRegex(Exception, 'Bucket name cannot be empty'):
            ActivityBucketDefinition.withBucketName('')