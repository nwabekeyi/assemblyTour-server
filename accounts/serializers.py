from rest_framework import serializers
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone')

    def create(self, validated_data):
        # Auto-generate registration ID
        reg_id = 'REG' + ''.join(random.choices(string.digits, k=6))

        # Auto-generate temporary password
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        # Create user
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            registration_id=reg_id
        )
        user.set_password(temp_password)
        user.save()

        # Attach temp password to user object for response
        user.temp_password = temp_password

        return user
