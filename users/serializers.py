from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id_user', 'role', 'first_name', 'last_name',
            'email', 'phone_number',
        ]


class AdminTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, style={'input_type': 'password'})

    default_error_messages = {
        'invalid_credentials': 'Unable to log in with provided credentials.',
        'not_admin': 'Access restricted to admin users only.',
    }

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')

        user = authenticate(request=request, email=email, password=password)
        if not user:
            self.fail('invalid_credentials')
        if user.role != 'admin':
            self.fail('not_admin')

        attrs['user'] = user
        return attrs
