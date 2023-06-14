from awx.main.models.inventory import Inventory
from awx.main.models.projects import Project
from awx.main.models.ha import InstanceGroup

from awx.main.models.jobs import JobTemplate
from awx.main.models.schedules import Schedule

{{ lookup("template", "awx_script_lib.py") }}

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
      container_group = InstanceGroup.objects.get(name="default")


      with AnsibleGetOrCreate(JobTemplate, name=job_name) as jt:
            jt.description = job_description
            jt.job_tags = job_tags
            jt.job_type = job_type
            jt.project = project
            jt.playbook = '{{ awx_template_jobs_playbook }}'
            jt.inventory = inventory
            jt.job_slice_count = {{ awx_template_jobs_slice_count }}
            jt.verbosity = {{ awx_template_jobs_verbosity }}
            jt.ask_limit_on_launch = True
            jt.ask_variables_on_launch = True
            jt.ask_job_type_on_launch = True  # i.e. --check or not
            jt.save()
            if not jt.instance_groups.filter(name=container_group.name):
                  jt.instance_groups.add(container_group)

            with AnsibleGetOrCreate(Schedule, name=job_schedule_name) as schedule:
                  schedule.unified_job_template=jt
                  schedule.name=job_schedule_name
                  schedule.rrule=job_schedule_rrule
