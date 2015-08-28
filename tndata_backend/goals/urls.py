from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(
        r'^$',
        views.IndexView.as_view(),
        name='index'
    ),

    # Custom Packages
    url(
        r'^accept-enrollment/complete/$',
        views.AcceptEnrollmentCompleteView.as_view(),
        name='accept-enrollment-complete'
    ),
    url(
        r'^accept-enrollment/(?P<pk>\d+)/$',
        views.accept_enrollment,
        name='accept-enrollment'
    ),
    url(
        r'^packages/(?P<pk>\d+)/enroll/$',
        views.PackageEnrollmentView.as_view(),
        name='package-enroll'
    ),
    url(
        r'^packages/(?P<pk>\d+)/$',
        views.PackageDetailView.as_view(),
        name='package-detail'
    ),
    url(
        r'^packages/$',
        views.PackageListView.as_view(),
        name='package-list'
    ),

    # Create views
    url(
        r'^new/categories/$',
        views.CategoryCreateView.as_view(),
        name='category-create'
    ),
    url(
        r'^new/triggers/$',
        views.TriggerCreateView.as_view(),
        name='trigger-create'
    ),
    url(
        r'^new/goals/$',
        views.GoalCreateView.as_view(),
        name='goal-create'
    ),
    url(
        r'^new/behavior/$',
        views.BehaviorCreateView.as_view(),
        name='behavior-create'
    ),
    url(
        r'^new/action/$',
        views.ActionCreateView.as_view(),
        name='action-create'
    ),
    url(
        r'^new/upload/$',
        views.upload_csv,
        name='upload-csv'
    ),

    # Actions
    url(
        r'^actions/$',
        views.ActionListView.as_view(),
        name='action-list'
    ),
    url(
        r'^actions/(?P<pk>\d+)-(?P<title_slug>.+)/publish/$',
        views.ActionPublishView.as_view(),
        name='action-publish'
    ),
    url(
        r'^actions/(?P<pk>\d+)-(?P<title_slug>.+)/update/$',
        views.ActionUpdateView.as_view(),
        name='action-update'
    ),
    url(
        r'^actions/(?P<pk>\d+)-(?P<title_slug>.+)/delete/$',
        views.ActionDeleteView.as_view(),
        name='action-delete'
    ),
    url(
        r'^actions/(?P<pk>\d+)-(?P<title_slug>.+)/duplicate/$',
        views.ActionDuplicateView.as_view(),
        name='action-duplicate'
    ),
    url(
        r'^actions/(?P<pk>\d+)-(?P<title_slug>.+)/$',
        views.ActionDetailView.as_view(),
        name='action-detail'
    ),

    # Behaviors
    url(
        r'^behaviors/$',
        views.BehaviorListView.as_view(),
        name='behavior-list'
    ),
    url(
        r'^behaviors/(?P<pk>\d+)-(?P<title_slug>.+)/publish/$',
        views.BehaviorPublishView.as_view(),
        name='behavior-publish'
    ),
    url(
        r'^behaviors/(?P<pk>\d+)-(?P<title_slug>.+)/update/$',
        views.BehaviorUpdateView.as_view(),
        name='behavior-update'
    ),
    url(
        r'^behaviors/(?P<pk>\d+)-(?P<title_slug>.+)/delete/$',
        views.BehaviorDeleteView.as_view(),
        name='behavior-delete'
    ),
    url(
        r'^behaviors/(?P<pk>\d+)-(?P<title_slug>.+)/duplicate/$',
        views.BehaviorDuplicateView.as_view(),
        name='behavior-duplicate'
    ),
    url(
        r'^behaviors/(?P<pk>\d+)-(?P<title_slug>.+)/$',
        views.BehaviorDetailView.as_view(),
        name='behavior-detail'
    ),

    # Triggers
    url(
        r'^triggers/$',
        views.TriggerListView.as_view(),
        name='trigger-list'
    ),
    url(
        r'^triggers/(?P<pk>\d+)-(?P<name_slug>.+)/update/$',
        views.TriggerUpdateView.as_view(),
        name='trigger-update'
    ),
    url(
        r'^triggers/(?P<pk>\d+)-(?P<name_slug>.+)/delete/$',
        views.TriggerDeleteView.as_view(),
        name='trigger-delete'
    ),
    url(
        r'^triggers/(?P<pk>\d+)-(?P<name_slug>.+)/duplicate/$',
        views.TriggerDuplicateView.as_view(),
        name='trigger-duplicate'
    ),
    url(
        r'^triggers/(?P<pk>\d+)-(?P<name_slug>.+)/$',
        views.TriggerDetailView.as_view(),
        name='trigger-detail'
    ),

    # Goals
    url(
        r'^goals/(?P<pk>\d+)-(?P<title_slug>.+)/publish/$',
        views.GoalPublishView.as_view(),
        name='goal-publish'
    ),
    url(
        r'^goals/(?P<pk>\d+)-(?P<title_slug>.+)/update/$',
        views.GoalUpdateView.as_view(),
        name='goal-update'
    ),
    url(
        r'^goals/(?P<pk>\d+)-(?P<title_slug>.+)/delete/$',
        views.GoalDeleteView.as_view(),
        name='goal-delete'
    ),
    url(
        r'^goals/(?P<pk>\d+)-(?P<title_slug>.+)/duplicate/$',
        views.GoalDuplicateView.as_view(),
        name='goal-duplicate'
    ),
    url(
        r'^goals/(?P<pk>\d+)-(?P<title_slug>.+)/$',
        views.GoalDetailView.as_view(),
        name='goal-detail'
    ),
    url(
        r'^goals/$',
        views.GoalListView.as_view(),
        name='goal-list'
    ),

    # Categories
    url(
        r'^categories/$',
        views.CategoryListView.as_view(),
        name='category-list'
    ),
    url(
        r'^categories/(?P<pk>\d+)-(?P<title_slug>.+)/publish/$',
        views.CategoryPublishView.as_view(),
        name='category-publish'
    ),
    url(
        r'^categories/(?P<pk>\d+)-(?P<title_slug>.+)/update/$',
        views.CategoryUpdateView.as_view(),
        name='category-update'
    ),
    url(
        r'^categories/(?P<pk>\d+)-(?P<title_slug>.+)/delete/$',
        views.CategoryDeleteView.as_view(),
        name='category-delete'
    ),
    url(
        r'^categories/(?P<pk>\d+)-(?P<title_slug>.+)/duplicate/$',
        views.CategoryDuplicateView.as_view(),
        name='category-duplicate'
    ),
    url(
        r'^categories/(?P<pk>\d+)-(?P<title_slug>.+)/$',
        views.CategoryDetailView.as_view(),
        name='category-detail'
    ),
)
