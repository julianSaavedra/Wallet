from src.model import Dollars, FinancialActivity

class ActivityBucketedAggregation:
    
    @classmethod
    def fromActivityCategories(cls):
        activityBucketingSpec = ActivityBucketingSpec.empty(useActivityCategoryAsDefault=True)
        return cls.withActivityBucketingSpec(activityBucketingSpec)

    @classmethod
    def withDefinition(cls, aBucketDefinition):
        activityBucketingSpec = ActivityBucketingSpec.withDefinition(aBucketDefinition, useActivityCategoryAsDefault=False)
        return cls.withActivityBucketingSpec(activityBucketingSpec) 
    
    @classmethod
    def withDefinitions(cls, bucketDefinitions):
        activityBucketingSpec = ActivityBucketingSpec.withDefinitions(bucketDefinitions, useActivityCategoryAsDefault=False)
        return cls.withActivityBucketingSpec(activityBucketingSpec) 

    @classmethod
    def withDefinitionDefaultingToActivityCategory(cls, aBucketDefinition):
        activityBucketingSpec = ActivityBucketingSpec.withDefinition(aBucketDefinition)
        return cls.withActivityBucketingSpec(activityBucketingSpec) 

    @classmethod
    def withDefinitionsDefaultingToActivityCategory(cls, bucketDefinitions):
        activityBucketingSpec = ActivityBucketingSpec.withDefinitions(bucketDefinitions, useActivityCategoryAsDefault=True)
        return cls.withActivityBucketingSpec(activityBucketingSpec) 

    @classmethod
    def withNoDefinitions(cls):
        activityBucketingSpec = ActivityBucketingSpec.empty(useActivityCategoryAsDefault=False)
        return cls.withActivityBucketingSpec(activityBucketingSpec)  

    @classmethod
    def withActivityBucketingSpec(cls, bucketingSpec):
        return cls(bucketingSpec)

    def __init__(self, spec):
        self._spec = spec

    def aggregatedResultsFromActivities(self, activities):
        aggregatedActivities = self.aggregatedActivitiesBasedOnSpec(activities)
        return self.totalsFromAggregatedActivities(aggregatedActivities)

    def aggregatedActivitiesBasedOnSpec(self, activities):
        aggregation = { bucket:[] for bucket in self.specBuckets() }
        for anActivity in activities:
            bucketDefinition = self.bucketDefinitionForActivity(anActivity)
            targetBucket = bucketDefinition.bucket()
            if targetBucket in aggregation:
                aggregation[targetBucket].append(anActivity)
            else: aggregation[targetBucket] = [ anActivity ]
        return aggregation

    def specBuckets(self):
        return self._spec.allBuckets() if self._spec else []

    def bucketDefinitionForActivity(self, anActivity):
        return self._spec.bucketDefinitionForActivity(anActivity)

    def totalsFromAggregatedActivities(self, aggregatedActivities):
        totalsAggregation = {}
        for category, activities in aggregatedActivities.items():
            totalForCategory = Dollars.zero()
            for anActivity in activities: totalForCategory = totalForCategory + anActivity.total()
            totalsAggregation[category] = ActivityBucket.withTotal(totalForCategory)
        return totalsAggregation


class ActivityBucket():

    @classmethod
    def withTotal(cls,total):
        return cls(total)
    
    def __init__(self, total):
        self._total = total

    def total(self):
        return self._total

class ActivityBucketDefinition:
    
    @classmethod
    def withBucketName(cls, bucketName):
        return cls.withBucketNameAndActivityCategories(bucketName, [])
    
    @classmethod
    def withBucketNameAndActivityCategories(cls, bucketName, activityCategories):
        cls.assertBucketNameNotEmpty(bucketName)
        return cls(bucketName, activityCategories)
    
    @classmethod
    def assertBucketNameNotEmpty(cls, bucketName):
        if not bucketName: raise Exception('Bucket name cannot be empty')

    def __init__(self, bucketName, activityCategories):
        self._bucketName = bucketName
        self._activityCategories = activityCategories

    def bucket(self):
        return self._bucketName

    def matches(self, anActivity):
        return anActivity.category() in self._activityCategories


class ActivityBucketingSpec:
    
    @classmethod
    def empty(cls, useActivityCategoryAsDefault=False):
        return cls.withDefinitions([], useActivityCategoryAsDefault)

    @classmethod
    def withDefinition(cls, aBucketDefinition, useActivityCategoryAsDefault=False):
        return cls.withDefinitions([aBucketDefinition], useActivityCategoryAsDefault)
    
    @classmethod
    def withDefinitions(cls, bucketDefinitions, useActivityCategoryAsDefault=False):
        return cls(bucketDefinitions, useActivityCategoryAsDefault)

    def __init__(self, aBucketDefinition, useActivityCategoryAsDefault):
        self._bucketDefinitions = aBucketDefinition
        self._useActivityCategoryAsDefault = useActivityCategoryAsDefault

    def allBuckets(self):
        return [aDefinition.bucket() for aDefinition in self._bucketDefinitions ]

    def bucketDefinitionForActivity(self, anActivity):
        for aDefinition in self._bucketDefinitions:
            if aDefinition.matches(anActivity): return aDefinition
        defaultBucket = anActivity.category() if self._useActivityCategoryAsDefault else 'NoBucket'
        return ActivityBucketDefinition.withBucketName(defaultBucket)
