# from django.db.models.signals import post_save
# from django.contrib.auth import get_user_model
# from django.dispatch import receiver
#
# User = get_user_model()
#
# @receiver(post_save, sender=User)
# def assign_role(sender, instance, created, **kwargs):
#     if created:
#         if instance.email.endswith("@virginia.edu"):
#             print(instance.email)
#             instance.is_staff = True
#         else:
#             instance.is_staff = False
#         instance.save()