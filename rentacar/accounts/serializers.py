from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, CustomerProfile, OwnerProfile

ALLOWED_REGISTER_ROLES = {User.Role.CUSTOMER, User.Role.OWNER}


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2', 'role']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate_role(self, value):
        if value not in ALLOWED_REGISTER_ROLES:
            raise serializers.ValidationError(
                "Invalid role. Registration is only allowed as customer or owner."
            )
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        validate_password(password, user=User(
            username=attrs.get('username', ''),
            email=attrs.get('email', ''),
        ))
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2') 

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        if user.role == User.Role.CUSTOMER:
            CustomerProfile.objects.create(user=user)
        elif user.role == User.Role.OWNER:
            OwnerProfile.objects.create(user=user)

        return user
    
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        data['user'] = user
        return data
    



class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'display_name', 'email', 'role',
            'is_superuser', 'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'is_superuser', 'is_active', 'date_joined']

    def get_display_name(self, obj):
        from rentacar.utils import format_display_name
        return format_display_name(obj.username)


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['id', 'user', 'profile_picture', 'phone_number', 'national_id_number', 'driving_license_number', 'address', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class OwnerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OwnerProfile
        fields = ['id', 'user', 'profile_picture', 'phone_number', 'national_id_number', 'address', 'is_verified', 'total_earnings', 'created_at']
        read_only_fields = ['id', 'user', 'is_verified', 'total_earnings', 'created_at']




class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, value):
        if value['new_password'] != value['new_password2']:
            raise serializers.ValidationError("New passwords do not match.")
        return value