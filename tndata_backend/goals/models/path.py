"""
Path-related functions for file/image upload fields.

"""
import hashlib
import os

from django.utils import timezone


def _upload_path(path_format, instance, filename):
    """Create an upload path (including a filename) for an uploaded file.

    * path_format: A format string for some object type. It should have accept
      one paramter: e.g. "/path/{}/dir/".
    * instance: the instance of the model containing a FileField or ImageField.
    * filename: original filename of the file.

    This function will create a new filename that is a hash of the original and
    the current time. Uploaded files whill always have a new filename.

    """
    original_filename, ext = os.path.splitext(filename)
    hash_content = "{}-{}".format(filename, timezone.now().strftime("%s"))
    filename = hashlib.md5(hash_content.encode("utf8")).hexdigest()
    if ext:
        filename += ext
    path = path_format.format(type(instance).__name__.lower())
    return os.path.join(path, filename)


def _category_icon_path(instance, filename):
    return _upload_path("goals/{}", instance, filename)


def _catetgory_image_path(instance, filename):
    return _upload_path("goals/{}/images", instance, filename)


def _goal_icon_path(instance, filename):
    return _upload_path("goals/{}", instance, filename)


def _behavior_icon_path(instance, filename):
    """Return the path for uploaded icons for `Behavior` and `Action` objects."""
    return _upload_path("goals/{}/icons", instance, filename)


def _behavior_img_path(instance, filename):
    """Return the path for uploaded images for `Behavior` and `Action` objects."""
    return _upload_path("goals/{}/images", instance, filename)
