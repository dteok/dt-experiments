import requests
import json

with open('../data/input/api_keys/usajobs_gov.json', 'r') as apifile:
    creds = json.load(apifile)

HOSTNAME = "data.usajobs.gov"
headers = {
  "Host": HOSTNAME,
  "User-Agent": creds.get('user_agent'),
  "Authorization-Key": creds.get('authorization_key')}

def Search(Keyword = None, PositionTitle = None, RemunerationMinimumAmount = None, RemunerationMaximumAmount = None, PayGradeHigh = None, PayGradeLow = None, JobCategoryCode = None, LocationName = None, PostingChannel = None, Organization = None, PositionOfferingTypeCode = None, TravelPercentage = None, PositionScheduleTypeCode = None, RelocationIndicator = None, SecurityClearanceRequired = None, SupervisoryStatus = None, DatePosted = None, JobGradeCode = None, SortField = None, SortDirection = None, Page = None, ResultsPerPage = None, WhoMayApply = None, Radius = None, Fields = None, SalaryBucket = None, GradeBucket = None, HiringPath = None, MissionCriticalTags = None, PositionSensitivity = None):
    params = {}
    if (Keyword):
        params["Keyword"] = Keyword
    if (PositionTitle):
        params["PositionTitle"] = PositionTitle
    if (RemunerationMinimumAmount):
        params["RemunerationMinimumAmount"] = RemunerationMinimumAmount
    if (RemunerationMaximumAmount):
        params["RemunerationMaximumAmount"] = RemunerationMaximumAmount
    if (PayGradeHigh):
        params["PayGradeHigh"] = PayGradeHigh
    if (PayGradeLow):
        params["PayGradeLow"] = PayGradeLow
    if (JobCategoryCode):
        params["JobCategoryCode"] = JobCategoryCode
    if (LocationName):
        params["LocationName"] = LocationName
    if (PostingChannel):
        params["PostingChannel"] = PostingChannel
    if (Organization):
        params["Organization"] = Organization
    if (PositionOfferingTypeCode):
        params["PositionOfferingTypeCode"] = PositionOfferingTypeCode
    if (TravelPercentage):
        params["TravelPercentage"] = TravelPercentage
    if (PositionScheduleTypeCode):
        params["PositionScheduleTypeCode"] = PositionScheduleTypeCode
    if (RelocationIndicator):
        params["RelocationIndicator"] = RelocationIndicator
    if (SecurityClearanceRequired):
        params["SecurityClearanceRequired"] = SecurityClearanceRequired
    if (SupervisoryStatus):
        params["SupervisoryStatus"] = SupervisoryStatus
    if (DatePosted):
        params["DatePosted"] = DatePosted
    if (JobGradeCode):
        params["JobGradeCode"] = JobGradeCode
    if (SortField):
        params["SortField"] = SortField
    if (SortDirection):
        params["SortDirection"] = SortDirection
    if (Page):
        params["Page"] = Page
    if (ResultsPerPage):
        params["ResultsPerPage"] = ResultsPerPage
    if (WhoMayApply):
        params["WhoMayApply"] = WhoMayApply
    if (Radius):
        params["Radius"] = Radius
    if (Fields):
        params["Fields"] = Fields
    if (SalaryBucket):
        params["SalaryBucket"] = SalaryBucket
    if (GradeBucket):
        params["GradeBucket"] = GradeBucket
    if (HiringPath):
        params["HiringPath"] = HiringPath
    if (MissionCriticalTags):
        params["MissionCriticalTags"] = MissionCriticalTags
    if (PositionSensitivity):
        params["PositionSensitivity"] = PositionSensitivity
    response = requests.get(f'https://{HOSTNAME}/api/search', headers=headers, params=params)
    return json.loads(response.content)

if (__name__ == '__main__'):
    print(Search(JobCategoryCode=2210)["status"])
