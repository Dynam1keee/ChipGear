from rest_framework import serializers

from goods.models import Category


def image_url(image_field):
    """Return the relative URL of an image, or None if there is no image."""
    return image_field.url if image_field else None


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image']

    def get_image(self, category):
        return image_url(category.image)
