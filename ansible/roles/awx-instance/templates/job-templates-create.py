from awx.main.models.inventory import Inventory
from awx.main.models.projects import Project
from awx.main.models.ha import InstanceGroup

from awx.main.models.jobs import JobTemplate
from awx.main.models.schedules import Schedule


def get_or_create_job_template(
    job_name,
    job_description,
    job_tags,
    job_type,
    job_schedule_name,
    job_schedule_rrule
):

      inventory = Inventory.objects.get(name="{{ awx_inventory_name }}")
      project = Project.objects.get(name="{{ awx_project_name }}")
      container_group = InstanceGroup.objects.get(name="{{ awx_elastic_container_group_name }}")

      changed = False

      try:
          jt = JobTemplate.objects.get(name=job_name)
      except JobTemplate.DoesNotExist:
          jt = JobTemplate.objects.create(
                  name=job_name,
                  description = job_description,
                  job_tags = job_tags,
                  job_type = job_type,
                  project = project,
                  playbook = '{{ awx_template_jobs_playbook }}',
                  inventory = inventory,
                  job_slice_count = {{ awx_template_jobs_slice_count }},
                  verbosity = {{ awx_template_jobs_verbosity }}
              )
          changed=True

      # Set instance group
      if not jt.instance_groups.filter(name=container_group.name):
          jt.instance_groups.add(container_group)
          changed=True

      # Set schedule for the job
      try:
          schedule = Schedule.objects.get(unified_job_template=jt, name=job_schedule_name)
      except Schedule.DoesNotExist:
          schedule = Schedule.objects.create(
              unified_job_template=jt,
              name=job_schedule_name,
              rrule=job_schedule_rrule
              )
          changed=True

      return changed
